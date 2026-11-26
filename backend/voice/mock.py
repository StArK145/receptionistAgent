"""Mock pipeline task used when Pipecat / WebRTC native libraries are unavailable."""

from typing import Any

from ..core.event_bus import EventBus


class MockPipelineTask:
    """Mock pipeline task ensuring the server runs smoothly in development/testing."""

    def __init__(self, webrtc_connection: Any, event_bus: EventBus):
        self.webrtc_connection = webrtc_connection
        self.event_bus = event_bus

    async def run(self):
        await self.event_bus.broadcast("bot_status", {
            "status": "ready",
            "message": "Mock bot session started (Pipecat simulated mode).",
        })
