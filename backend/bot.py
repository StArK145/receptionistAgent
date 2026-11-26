"""Small Pipecat voice pipeline for the clinic receptionist."""

import logging
from typing import Any

from .core.config import (
    get_elevenlabs_api_key,
    get_elevenlabs_voice_id,
)
from .core.event_bus import EventBus, global_event_bus
from .voice.prompts import RECEPTIONIST_SYSTEM_PROMPT
from .voice.tool_registry import TOOL_SCHEMAS, build_llm_tools, handle_tool_call
from .voice.providers.pipecat_imports import (
    PIPECAT_AVAILABLE, SileroVADAnalyzer, Pipeline, PipelineTask,
    PipelineParams, LLMContext, LLMContextAggregatorPair,
    SmallWebRTCTransport, TransportParams,
    ElevenLabsRealtimeSTTService, ElevenLabsSTTService,
    CommitStrategy,
    ElevenLabsTTSService,
)
from .voice.providers.llm import create_llm_service

logger = logging.getLogger(__name__)


class _TranscriptObserver:
    """Installed as a Pipecat processor when available; forwards transcript frames."""

    def __new__(cls, event_bus: EventBus):
        # Delay Pipecat imports so API-only installs can still import this module.
        try:
            from pipecat.processors.frame_processor import FrameProcessor
            from pipecat.frames.frames import TranscriptionFrame, InterimTranscriptionFrame, TextFrame
        except ImportError:
            return None

        class Observer(FrameProcessor):
            async def process_frame(self, frame, direction):
                await super().process_frame(frame, direction)
                if isinstance(frame, (TranscriptionFrame, InterimTranscriptionFrame)):
                    text = getattr(frame, "text", "").strip()
                    if text:
                        await event_bus.broadcast("caller_transcript", {
                            "text": text, "is_final": isinstance(frame, TranscriptionFrame),
                        })
                elif isinstance(frame, TextFrame):
                    text = getattr(frame, "text", "").strip()
                    if text:
                        await event_bus.broadcast("agent_transcript", {"text": text})
                await self.push_frame(frame, direction)

        return Observer()


def create_bot_pipeline(
    webrtc_connection: Any,
    event_bus: EventBus = global_event_bus,
    aiohttp_session: Any = None,
) -> Any:
    """Create the direct transport → speech → LLM → speech pipeline."""
    if not PIPECAT_AVAILABLE:
        from .voice.mock import MockPipelineTask
        return MockPipelineTask(webrtc_connection, event_bus)

    vad = SileroVADAnalyzer()
    transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        params=TransportParams(audio_in_enabled=True, audio_out_enabled=True),
    )

    key = get_elevenlabs_api_key()
    session = aiohttp_session
    stt = None
    if ElevenLabsRealtimeSTTService:
        try:
            stt = ElevenLabsRealtimeSTTService(
                api_key=key,
                **({"commit_strategy": CommitStrategy.VAD} if CommitStrategy else {}),
            )
        except Exception:
            logger.exception("Realtime ElevenLabs STT setup failed; trying standard STT")
    if stt is None and ElevenLabsSTTService and session is not None:
        stt = ElevenLabsSTTService(api_key=key, aiohttp_session=session)
    if stt is None:
        raise RuntimeError("ElevenLabs STT needs an available service and HTTP session")

    llm = create_llm_service(system_instruction=RECEPTIONIST_SYSTEM_PROMPT)
    context = LLMContext(messages=[], tools=build_llm_tools(event_bus, llm))
    try:
        from pipecat.processors.aggregators.llm_response_universal import LLMUserAggregatorParams
        aggregators = LLMContextAggregatorPair(
            context, user_params=LLMUserAggregatorParams(vad_analyzer=vad),
        )
    except (ImportError, TypeError):
        aggregators = LLMContextAggregatorPair(context)
    tts = ElevenLabsTTSService(
        api_key=key,
        settings=ElevenLabsTTSService.Settings(voice=get_elevenlabs_voice_id()),
    )

    observer = _TranscriptObserver(event_bus)
    processors = [transport.input(), stt]
    if observer:
        processors.append(observer)
    processors.extend([
        aggregators.user(), llm, tts, transport.output(), aggregators.assistant(),
    ])
    task = PipelineTask(Pipeline(processors), params=PipelineParams())

    @transport.event_handler("on_client_connected")
    async def on_client_connected(_transport, client):
        await event_bus.broadcast("bot_status", {"status": "connected"})

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(_transport, client):
        await event_bus.broadcast("bot_status", {"status": "disconnected"})

    return task


__all__ = [
    "EventBus", "global_event_bus", "RECEPTIONIST_SYSTEM_PROMPT", "TOOL_SCHEMAS",
    "handle_tool_call", "create_bot_pipeline", "PIPECAT_AVAILABLE",
]
