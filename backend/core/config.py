"""Centralized environment and path configuration for the Voice Doctor Assistant backend."""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_DB_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(BACKEND_DIR, "doctor_assistant.db"),
)


def get_gemini_api_key() -> Optional[str]:
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")


def get_gemini_model() -> str:
    return os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")


def get_openrouter_api_key() -> Optional[str]:
    return os.environ.get("OPENROUTER_API_KEY")


def get_openrouter_model() -> str:
    return os.environ.get("OPENROUTER_MODEL", "google/gemini-2.5-flash")


def get_elevenlabs_api_key() -> Optional[str]:
    return os.environ.get("ELEVENLABS_API_KEY")


def get_elevenlabs_voice_id() -> str:
    return os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
