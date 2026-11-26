"""Dynamic Pipecat imports with graceful fallback when Pipecat is not installed."""

import logging

logger = logging.getLogger(__name__)

try:
    from pipecat.audio.vad.silero import SileroVADAnalyzer
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.pipeline.task import PipelineTask, PipelineParams
    from pipecat.frames.frames import (
        Frame,
        TextFrame,
        TranscriptionFrame,
        InterimTranscriptionFrame,
        InputAudioRawFrame,
        VADUserStartedSpeakingFrame,
        VADUserStoppedSpeakingFrame,
        InterruptionFrame,
        BotStartedSpeakingFrame,
        BotStoppedSpeakingFrame,
        TTSStartedFrame,
        TTSStoppedFrame,
    )
    try:
        from pipecat.frames.frames import LLMFullResponseStartFrame
    except ImportError:
        LLMFullResponseStartFrame = None
    try:
        from pipecat.frames.frames import LLMFullResponseEndFrame
    except ImportError:
        LLMFullResponseEndFrame = None
    try:
        from pipecat.frames.frames import LLMMessagesAppendFrame
    except ImportError:
        try:
            from pipecat.frames.frames import LLMMessagesFrame as LLMMessagesAppendFrame
        except ImportError:
            LLMMessagesAppendFrame = None

    from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
    from pipecat.processors.aggregators.llm_context import LLMContext
    from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
    from pipecat.services.google.llm import GoogleLLMService

    try:
        from pipecat.services.openrouter.llm import OpenRouterLLMService, OpenRouterProviderPreferences
    except ImportError:
        try:
            from pipecat.services.openrouter.llm import OpenRouterLLMService
        except ImportError:
            OpenRouterLLMService = None
        OpenRouterProviderPreferences = None

    from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
    try:
        from pipecat.services.elevenlabs.tts import ElevenLabsHttpTTSService
    except ImportError:
        ElevenLabsHttpTTSService = None

    try:
        from pipecat.transcriptions.language import Language
    except ImportError:
        Language = None

    try:
        from pipecat.services.elevenlabs.stt import ElevenLabsRealtimeSTTService, CommitStrategy
    except ImportError:
        ElevenLabsRealtimeSTTService = None
        CommitStrategy = None

    try:
        from pipecat.services.elevenlabs.stt import ElevenLabsSTTService
    except ImportError:
        ElevenLabsSTTService = ElevenLabsRealtimeSTTService

    from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport, TransportParams
    from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection

    PIPECAT_AVAILABLE = True
except ImportError as err:
    logger.warning("Pipecat modules not found or incomplete (%s). Running in mock/simulation-ready mode.", err)
    PIPECAT_AVAILABLE = False
    FrameProcessor = object
    Frame = object
    FrameDirection = object
    InputAudioRawFrame = None
    VADUserStartedSpeakingFrame = None
    VADUserStoppedSpeakingFrame = None
    SileroVADAnalyzer = None
    Pipeline = None
    PipelineRunner = None
    PipelineTask = None
    PipelineParams = None
    LLMMessagesAppendFrame = None
    LLMContext = None
    LLMContextAggregatorPair = None
    GoogleLLMService = None
    OpenRouterLLMService = None
    OpenRouterProviderPreferences = None
    ElevenLabsTTSService = None
    ElevenLabsHttpTTSService = None
    Language = None
    ElevenLabsRealtimeSTTService = None
    CommitStrategy = None
    ElevenLabsSTTService = None
    SmallWebRTCTransport = None
    TransportParams = None
    SmallWebRTCConnection = None
