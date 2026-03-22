import json
import asyncio
from collections import defaultdict
from typing import Any

from fastapi import WebSocket

from app.core.config import get_settings

settings = get_settings()


class WebSocketManager:
    """Room-based WebSocket manager with Redis pub/sub bridge."""

    def __init__(self):
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)
        self._redis: Any = None
        self._pubsub_task: asyncio.Task | None = None

    async def startup(self):
        if settings.desktop_mode:
            return  # No Redis needed in desktop mode
        import redis.asyncio as aioredis
        self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        self._pubsub_task = asyncio.create_task(self._listen_redis())

    async def shutdown(self):
        if self._pubsub_task:
            self._pubsub_task.cancel()
        if self._redis:
            await self._redis.aclose()

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        self._rooms[room].add(websocket)

    def disconnect(self, websocket: WebSocket, room: str):
        self._rooms[room].discard(websocket)
        if not self._rooms[room]:
            del self._rooms[room]

    async def broadcast_to_room(self, room: str, event: str, data: Any):
        message = json.dumps({"event": event, "data": data})
        dead = []
        for ws in self._rooms.get(room, set()):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._rooms[room].discard(ws)

    async def publish(self, room: str, event: str, data: Any):
        """Publish event — direct broadcast in desktop mode, Redis pub/sub otherwise."""
        if settings.desktop_mode:
            await self.broadcast_to_room(room, event, data)
        elif self._redis:
            payload = json.dumps({"room": room, "event": event, "data": data})
            await self._redis.publish("ws:events", payload)

    async def _listen_redis(self):
        """Subscribe to Redis and forward to WebSocket rooms."""
        if not self._redis:
            return
        pubsub = self._redis.pubsub()
        await pubsub.subscribe("ws:events")
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    payload = json.loads(message["data"])
                    await self.broadcast_to_room(
                        payload["room"], payload["event"], payload["data"]
                    )
        except asyncio.CancelledError:
            await pubsub.unsubscribe("ws:events")


ws_manager = WebSocketManager()
