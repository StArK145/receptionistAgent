"""Core infrastructure package (configuration and pub/sub event bus)."""

from .config import (
    BACKEND_DIR,
    DEFAULT_DB_PATH,
    get_gemini_api_key,
    get_gemini_model,
    get_openrouter_api_key,
    get_openrouter_model,
    get_elevenlabs_api_key,
    get_elevenlabs_voice_id,
)
from .event_bus import EventBus, global_event_bus

__all__ = [
    "BACKEND_DIR",
    "DEFAULT_DB_PATH",
    "get_gemini_api_key",
    "get_gemini_model",
    "get_openrouter_api_key",
    "get_openrouter_model",
    "get_elevenlabs_api_key",
    "get_elevenlabs_voice_id",
    "EventBus",
    "global_event_bus",
]
