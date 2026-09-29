"""Live Feed — Server-Sent Events for real-time messages."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import AsyncGenerator

import structlog

logger = structlog.get_logger()


class LiveFeed:
    """Broadcast real-time events to admin dashboards."""

    def __init__(self):
        self.clients: list[asyncio.Queue] = []
        self.history: list[dict] = []
        self.max_history = 100
        self.total_events = 0

    async def subscribe(self) -> AsyncGenerator[str, None]:
        """Subscribe to live feed (SSE generator)."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.clients.append(queue)
        
        client_count = len(self.clients)
        logger.info("live_feed.subscribe", total_clients=client_count)

        try:
            # Send connection confirmation
            yield f"data: {json.dumps({'type': 'connected', 'clients': client_count})}\n\n"
            
            # Send last 20 events as history
            for event in self.history[-20:]:
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            # Stream new events
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=25)
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    # Heartbeat to keep connection alive
                    yield f": heartbeat {datetime.now(timezone.utc).isoformat()}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if queue in self.clients:
                self.clients.remove(queue)
            logger.info("live_feed.unsubscribe", remaining=len(self.clients))

    async def broadcast(self, event: dict):
        """Broadcast event to all connected clients."""
        event["timestamp"] = datetime.now(timezone.utc).isoformat()
        self.total_events += 1
        event["id"] = self.total_events
        
        # Save to history
        self.history.append(event)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        # Send to all clients
        dead_clients = []
        for queue in self.clients:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                dead_clients.append(queue)
        
        # Cleanup full queues
        for queue in dead_clients:
            if queue in self.clients:
                self.clients.remove(queue)
        
        logger.info(
            "live_feed.broadcast",
            event_type=event.get("type"),
            clients=len(self.clients),
        )

    def stats(self) -> dict:
        """Get live feed stats."""
        return {
            "connected_clients": len(self.clients),
            "total_events": self.total_events,
            "history_size": len(self.history),
        }


# Singleton
live_feed = LiveFeed()
