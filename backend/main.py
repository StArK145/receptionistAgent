"""FastAPI entrypoint for WebRTC, clinic data, and live events."""

import logging
from contextlib import asynccontextmanager

import aiohttp
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from .db import init_db, seed_database
from .api import webrtc_router, clinic_router, events_router
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes database and shared aiohttp session on server start."""
    init_db()
    seed_result = seed_database()
    app.state.seed_info = seed_result
    logger.info("Database initialized and verified on startup: %s", seed_result)

    async with aiohttp.ClientSession() as session:
        app.state.aiohttp_session = session
        yield


app = FastAPI(
    title="Voice Doctor Assistant API",
    description="Pipecat Voice Assistant WebRTC Signaling, Event Streaming, and Doctor Appointment API.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webrtc_router)
app.include_router(clinic_router)
app.include_router(events_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
