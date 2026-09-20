import asyncio
import json
from typing import Set

from fastapi import WebSocket


class ConnectionManager:
    """Hub de WebSockets para el panel en tiempo real."""

    def __init__(self) -> None:
        self.active: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self.active.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self.active.discard(websocket)

    async def broadcast(self, event: str, data: dict) -> None:
        if not self.active:
            return
        message = json.dumps({"event": event, "data": data}, default=str)
        dead = []
        for websocket in list(self.active):
            try:
                await websocket.send_text(message)
            except Exception:
                dead.append(websocket)
        for websocket in dead:
            await self.disconnect(websocket)

    @property
    def connections(self) -> int:
        return len(self.active)


manager = ConnectionManager()
