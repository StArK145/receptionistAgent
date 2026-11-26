"""Real-time pub/sub EventBus for streaming transcripts, tool calls, and booking events."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Set


class EventBus:
    """Pub/Sub event broadcaster for live pipeline events."""

    def __init__(self):
        self._subscribers: Set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue(maxsize=200)
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subscribers.discard(q)

    async def broadcast(self, event_type: str, data: Dict[str, Any]) -> None:
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        dead: List[asyncio.Queue] = []
        for q in list(self._subscribers):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                try:
                    _ = q.get_nowait()
                    q.put_nowait(event)
                except Exception:
                    dead.append(q)
            except Exception:
                dead.append(q)

        for q in dead:
            self._subscribers.discard(q)


# Singleton event bus instance shared across API routes and the voice pipeline
global_event_bus = EventBus()
