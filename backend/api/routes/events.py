"""Live SSE event stream and system health endpoints."""

import json
import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from ...core.config import DEFAULT_DB_PATH
from ...core.event_bus import global_event_bus
from ...db import get_all_doctors, get_all_appointments
from ...voice import PIPECAT_AVAILABLE

router = APIRouter()


@router.get("/api/events", tags=["Live Events"])
async def live_events_sse(request: Request):
    """
    Server-Sent Events (SSE) endpoint streaming real-time pipeline events:
    caller_transcript, agent_transcript, tool_call_start, tool_call_result,
    appointment_booked, appointment_cancelled, and bot_status.
    """
    queue = global_event_bus.subscribe()

    async def event_generator():
        try:
            init_data = json.dumps({
                "type": "connected",
                "data": {"message": "Subscribed to live Voice Assistant event stream."},
                "timestamp": asyncio.get_event_loop().time(),
            })
            yield f"data: {init_data}\n\n"

            while True:
                if await request.is_disconnected():
                    break

                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"

        except asyncio.CancelledError:
            pass
        finally:
            global_event_bus.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/health", tags=["System"])
async def health_check():
    """Returns system status and DB health."""
    doctors = get_all_doctors()
    appointments = get_all_appointments()
    return {
        "status": "healthy",
        "service": "Voice Doctor Assistant Backend",
        "pipecat_loaded": PIPECAT_AVAILABLE,
        "database": DEFAULT_DB_PATH,
        "doctors_count": len(doctors),
        "total_appointments": len(appointments),
    }
