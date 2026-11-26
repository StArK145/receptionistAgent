"""Pipecat full-duplex voice pipeline assembly and turn/connection lifecycle handlers."""

import re
import logging
import asyncio
from typing import Any

from ..core.config import get_elevenlabs_api_key, get_elevenlabs_voice_id
from ..core.event_bus import EventBus, global_event_bus
from .audio_track import install_smooth_audio_track
from .prompts import RECEPTIONIST_SYSTEM_PROMPT, CLINIC_KEYTERMS
from .tool_registry import build_llm_tools
from .mock import MockPipelineTask
from .providers import create_stt_service, create_llm_service, create_tts_service
from .providers.pipecat_imports import (
    PIPECAT_AVAILABLE,
    SileroVADAnalyzer,
    Pipeline,
    PipelineTask,
    PipelineParams,
    LLMMessagesAppendFrame,
    LLMContext,
    LLMContextAggregatorPair,
    SmallWebRTCTransport,
    TransportParams,
)

try:
    from loguru import logger
except ImportError:  # pragma: no cover
    logger = logging.getLogger(__name__)


def _create_vad_analyzer() -> Any:
    """Creates the Silero VAD analyzer calibrated for normal full-duplex phone speech."""
    try:
        from pipecat.audio.vad.vad_analyzer import VADParams
        return SileroVADAnalyzer(
            params=VADParams(
                confidence=0.62,
                start_secs=0.2,
                stop_secs=0.2,
                min_volume=0.2,
            )
        )
    except Exception:
        return SileroVADAnalyzer()


def _create_context_aggregator(context: Any, vad_analyzer: Any) -> Any:
    """Configures full-duplex user turn start/stop strategies and returns LLMContextAggregatorPair."""
    try:
        from pipecat.turns.user_start import VADUserTurnStartStrategy, TranscriptionUserTurnStartStrategy
        from pipecat.turns.user_stop import SpeechTimeoutUserTurnStopStrategy
        from pipecat.processors.aggregators.llm_response_universal import (
            LLMUserAggregatorParams,
            UserTurnStrategies,
        )
        user_params = LLMUserAggregatorParams(
            user_turn_strategies=UserTurnStrategies(
                start=[
                    VADUserTurnStartStrategy(enable_interruptions=True),
                    TranscriptionUserTurnStartStrategy(enable_interruptions=True, use_interim=True),
                ],
                stop=[
                    SpeechTimeoutUserTurnStopStrategy(user_speech_timeout=0.45),
                ],
            ),
            user_turn_stop_timeout=8.0,
            vad_analyzer=vad_analyzer,
        )
        return LLMContextAggregatorPair(context, user_params=user_params)
    except Exception as e:
        logger.warning(f"Could not customize LLMUserAggregatorParams: {e}")
        try:
            from pipecat.processors.aggregators.llm_response_universal import LLMUserAggregatorParams
            return LLMContextAggregatorPair(
                context,
                user_params=LLMUserAggregatorParams(vad_analyzer=vad_analyzer),
            )
        except Exception:
            return LLMContextAggregatorPair(context)


def create_bot_pipeline(
    webrtc_connection: Any,
    event_bus: EventBus = global_event_bus,
    aiohttp_session: Any = None,
) -> Any:
    """
    Constructs and returns the complete full-duplex Pipecat pipeline task:
    SmallWebRTCTransport -> ElevenLabs STT -> UserAggregator -> LLM -> ElevenLabs TTS -> Transport Output -> AssistantAggregator
    """
    if not PIPECAT_AVAILABLE:
        logger.info("Pipecat is not installed in the current environment. Returning mock pipeline task.")
        return MockPipelineTask(webrtc_connection, event_bus)

    elevenlabs_key = get_elevenlabs_api_key()
    tts_voice_id = get_elevenlabs_voice_id()

    # 1. VAD & SmallWebRTC Transport (browser WebRTC handles AEC/NS/AGC)
    vad_analyzer = _create_vad_analyzer()
    transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            audio_out_sample_rate=48000,
            audio_in_filter=None,
            audio_out_auto_silence=True,
        ),
    )
    install_smooth_audio_track(transport)

    # 2. AI Services (STT, LLM, Tools, TTS)
    stt = create_stt_service(
        elevenlabs_key=elevenlabs_key,
        aiohttp_session=aiohttp_session,
        keyterms=CLINIC_KEYTERMS,
    )
    llm = create_llm_service(system_instruction=RECEPTIONIST_SYSTEM_PROMPT)
    tools = build_llm_tools(event_bus=event_bus, llm=llm)
    tts = create_tts_service(
        elevenlabs_key=elevenlabs_key,
        voice_id=tts_voice_id,
        aiohttp_session=aiohttp_session,
    )

    # 3. Context Aggregators & Live Transcript Events
    context = LLMContext(messages=[], tools=tools)
    context_aggregator = _create_context_aggregator(context, vad_analyzer)
    user_aggregator = context_aggregator.user()
    assistant_aggregator = context_aggregator.assistant()

    last_caller_text = ""
    last_caller_time = 0.0

    @user_aggregator.event_handler("on_user_turn_stopped")
    async def on_user_turn_stopped(aggregator, strategy, message):
        nonlocal last_caller_text, last_caller_time
        raw_text = (getattr(message, "content", None) or "").strip()
        cleaned = re.sub(r"\[.*?\]", "", raw_text).strip()
        now = asyncio.get_running_loop().time()
        if cleaned and (cleaned != last_caller_text or (now - last_caller_time) > 2.5):
            last_caller_text = cleaned
            last_caller_time = now
            await event_bus.broadcast("caller_transcript", {
                "text": cleaned,
                "is_final": True,
            })

    @assistant_aggregator.event_handler("on_assistant_turn_stopped")
    async def on_assistant_turn_stopped(aggregator, message):
        text = (getattr(message, "content", None) or "").strip()
        if text:
            await event_bus.broadcast("agent_transcript", {
                "text": text,
            })

    # 4. Assemble Pipeline & Task
    pipeline = Pipeline([
        transport.input(),
        stt,
        user_aggregator,
        llm,
        tts,
        transport.output(),
        assistant_aggregator,
    ])
    task = PipelineTask(pipeline, params=PipelineParams(enable_metrics=True))

    # 5. Connection & Greeting Lifecycle
    initial_greeting_sent = False

    async def _trigger_greeting(client=None):
        nonlocal initial_greeting_sent
        if initial_greeting_sent:
            return
        initial_greeting_sent = True
        logger.info("WebRTC client connected. Triggering receptionist greeting.")
        await event_bus.broadcast("bot_status", {"status": "connected", "client": str(client or "caller")})
        if LLMMessagesAppendFrame:
            greeting_msg = [
                {
                    "role": "user",
                    "content": "The caller has just connected to Metro Health Clinic. Greet them warmly in 1 short sentence and ask how you can help.",
                }
            ]
            try:
                frame = LLMMessagesAppendFrame(greeting_msg, run_llm=True)
            except TypeError:
                frame = LLMMessagesAppendFrame(greeting_msg)
            await task.queue_frames([frame])

    async def _auto_greet():
        await asyncio.sleep(1.2)
        if not initial_greeting_sent:
            await _trigger_greeting("auto-start")

    auto_greet_task = asyncio.create_task(_auto_greet())

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        await _trigger_greeting(client)

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("WebRTC client disconnected.")
        if not auto_greet_task.done():
            auto_greet_task.cancel()
        await event_bus.broadcast("bot_status", {"status": "disconnected"})
        await task.cancel()

    return task
