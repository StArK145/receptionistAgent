"""WebRTC SDP signaling route (POST /api/offer)."""

import asyncio
import logging
from fastapi import APIRouter, Request, BackgroundTasks

from ...core.event_bus import global_event_bus
from ...bot import create_bot_pipeline, PIPECAT_AVAILABLE
from ...voice.providers.pipecat_imports import SmallWebRTCConnection, PipelineRunner
from ..schemas import WebRTCOfferRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["WebRTC Signaling"])


@router.post("/api/offer")
async def webrtc_offer(
    http_request: Request,
    body: WebRTCOfferRequest,
    background_tasks: BackgroundTasks,
):
    """
    WebRTC SDP offer/answer negotiation with SmallWebRTCConnection.
    Client sends SDP offer; server creates peer connection, boots Pipecat bot pipeline,
    and returns SDP answer.
    """
    logger.info("Received WebRTC offer: type=%s, length=%d", body.type, len(body.sdp))

    await global_event_bus.broadcast("webrtc_signaling", {
        "event": "offer_received",
        "sdp_type": body.type,
    })

    if PIPECAT_AVAILABLE and SmallWebRTCConnection and PipelineRunner:
        try:
            connection = SmallWebRTCConnection(ice_servers=["stun:stun.l.google.com:19302"])

            await connection.initialize(body.sdp, body.type)
            answer = connection.get_answer()
            if asyncio.iscoroutine(answer):
                answer = await answer

            aiohttp_session = getattr(http_request.app.state, "aiohttp_session", None)
            task = create_bot_pipeline(
                webrtc_connection=connection,
                event_bus=global_event_bus,
                aiohttp_session=aiohttp_session,
            )
            runner = PipelineRunner(handle_sigint=False)
            background_tasks.add_task(runner.run, task)

            logger.info("SmallWebRTC connection initialized successfully.")
            if isinstance(answer, dict):
                return answer
            return {
                "sdp": getattr(answer, "sdp", str(answer)),
                "type": getattr(answer, "type", "answer"),
            }
        except Exception as e:
            logger.exception("Error negotiating SmallWebRTC connection: %s", e)
            return {
                "mode": "simulation",
                "type": "answer",
                "message": f"Operating in simulation mode: {str(e)}",
            }

    logger.warning("Running WebRTC in simulation mode (Pipecat / SmallWebRTC not loaded).")
    await global_event_bus.broadcast("bot_status", {
        "status": "ready",
        "message": "WebRTC offer received. Operating in simulation mode.",
    })
    return {
        "mode": "simulation",
        "type": "answer",
        "message": "Offer accepted in simulation mode.",
    }
