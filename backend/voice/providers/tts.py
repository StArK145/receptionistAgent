"""Text-to-Speech provider factory (ElevenLabs HTTP streaming primary, WebSocket fallback)."""

import logging
from typing import Any, Optional

from .pipecat_imports import ElevenLabsHttpTTSService, ElevenLabsTTSService

logger = logging.getLogger(__name__)


def create_tts_service(
    elevenlabs_key: Optional[str],
    voice_id: str,
    aiohttp_session: Any = None,
) -> Any:
    """
    Creates ElevenLabsHttpTTSService (eleven_flash_v2_5) when a pooled aiohttp_session
    is available, falling back to ElevenLabsTTSService otherwise.
    """
    if ElevenLabsHttpTTSService and aiohttp_session is not None:
        logger.info("Using ElevenLabsHttpTTSService (eleven_flash_v2_5, optimize_streaming_latency=1)")
        return ElevenLabsHttpTTSService(
            api_key=elevenlabs_key,
            aiohttp_session=aiohttp_session,
            settings=ElevenLabsHttpTTSService.Settings(
                voice=voice_id,
                model="eleven_flash_v2_5",
                optimize_streaming_latency=1,
            ),
        )

    if hasattr(ElevenLabsTTSService, "Settings"):
        logger.info("Using ElevenLabsTTSService fallback (eleven_flash_v2_5)")
        return ElevenLabsTTSService(
            api_key=elevenlabs_key,
            settings=ElevenLabsTTSService.Settings(
                voice=voice_id,
                model="eleven_flash_v2_5",
            ),
        )

    return ElevenLabsTTSService(
        api_key=elevenlabs_key,
        voice_id=voice_id,
        model="eleven_flash_v2_5",
    )
