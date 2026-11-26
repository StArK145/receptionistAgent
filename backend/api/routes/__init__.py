"""API route modules."""

from .webrtc import router as webrtc_router
from .clinic import router as clinic_router
from .events import router as events_router

__all__ = ["webrtc_router", "clinic_router", "events_router"]
