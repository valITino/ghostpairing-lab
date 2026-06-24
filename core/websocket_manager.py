"""
WebSocket connection manager for real-time attack monitoring.
Thread-safe with dead connection cleanup.
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Set, Any

from fastapi import WebSocket


class WebSocketManager:
    """Manages WebSocket connections for monitoring dashboards."""

    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()
        self._attack_info: Dict[str, dict] = {}

    async def connect(self, websocket: WebSocket, client_id: str = None) -> str:
        """Accept a new WebSocket connection and return its client ID."""
        await websocket.accept()
        cid = client_id or f"monitor_{uuid.uuid4().hex[:8]}"
        async with self._lock:
            self._connections.setdefault(cid, set()).add(websocket)
            self._attack_info[cid] = {
                "connected_at": datetime.now().isoformat(),
                "status": "connected",
            }
        return cid

    async def disconnect(self, websocket: WebSocket, client_id: str) -> None:
        """Remove a disconnected WebSocket."""
        async with self._lock:
            conns = self._connections.get(client_id, set())
            conns.discard(websocket)
            if not conns:
                self._connections.pop(client_id, None)
                self._attack_info.pop(client_id, None)

    async def send_personal(self, message: dict, client_id: str) -> None:
        """Send a JSON message to all connections for a given client."""
        stale = set()
        for ws in self._connections.get(client_id, set()):
            try:
                await ws.send_json(message)
            except Exception:
                stale.add(ws)
        for ws in stale:
            self._connections.get(client_id, set()).discard(ws)

    async def broadcast(self, message: dict) -> None:
        """Send a JSON message to all connected clients."""
        for cid in list(self._connections.keys()):
            await self.send_personal(message, cid)

    def get_attack_info(self, client_id: str) -> dict:
        """Get info about a connected client."""
        return self._attack_info.get(client_id, {})

    @property
    def active_count(self) -> int:
        return len(self._connections)


# Singleton
ws_manager = WebSocketManager()
