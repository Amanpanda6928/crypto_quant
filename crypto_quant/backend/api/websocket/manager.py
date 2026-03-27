from fastapi import WebSocket
from typing import Dict, List
import asyncio


class ConnectionManager:
    """
    Advanced WebSocket manager:
    - Supports channels (e.g., BTCUSDT, signals)
    - Handles concurrency safely
    - Cleans dead connections
    """

    def __init__(self):
        # channel -> list of websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

        # lock for thread safety
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        await websocket.accept()

        async with self._lock:
            if channel not in self.active_connections:
                self.active_connections[channel] = []

            self.active_connections[channel].append(websocket)

    async def disconnect(self, websocket: WebSocket, channel: str) -> None:
        async with self._lock:
            if channel in self.active_connections:
                if websocket in self.active_connections[channel]:
                    self.active_connections[channel].remove(websocket)

                # cleanup empty channel
                if not self.active_connections[channel]:
                    del self.active_connections[channel]

    async def send_personal(self, websocket: WebSocket, data: dict) -> None:
        try:
            await websocket.send_json(data)
        except Exception:
            pass

    async def broadcast(self, channel: str, data: dict) -> None:
        """
        Send message only to subscribers of a specific channel.
        """

        async with self._lock:
            connections = self.active_connections.get(channel, []).copy()

        disconnected = []

        for connection in connections:
            try:
                await connection.send_json(data)
            except Exception:
                disconnected.append(connection)

        # cleanup disconnected
        for conn in disconnected:
            await self.disconnect(conn, channel)
