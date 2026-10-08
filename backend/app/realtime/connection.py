import asyncio
import logging
from contextlib import suppress
from typing import Any

from starlette.websockets import WebSocket

from app.realtime.protocol import CLOSE_INTERNAL, encode_frame

logger = logging.getLogger(__name__)

SEND_TIMEOUT_S = 5.0
CLOSE_TIMEOUT_S = 2.0


async def safe_send(websocket: WebSocket, frame: dict[str, Any]) -> None:
    """Pre-auth send: best effort, never raises."""
    with suppress(Exception):
        await websocket.send_text(encode_frame(frame))


async def safe_close(websocket: WebSocket, code: int, reason: str = "") -> None:
    with suppress(Exception):
        await asyncio.wait_for(websocket.close(code=code, reason=reason), CLOSE_TIMEOUT_S)


class Connection:
    """One authenticated socket. Sends are serialized and time-boxed so a slow client
    can never block a broadcast or interleave frames."""

    def __init__(self, websocket: WebSocket, *, user_id: str, session_id: str) -> None:
        self.websocket = websocket
        self.user_id = user_id
        self.session_id = session_id
        self.closed = False
        self._send_lock = asyncio.Lock()

    async def send(self, frame: dict[str, Any]) -> bool:
        return await self.send_text(encode_frame(frame))

    async def send_text(self, data: str) -> bool:
        if self.closed:
            return False
        try:
            async with self._send_lock:
                await asyncio.wait_for(self.websocket.send_text(data), SEND_TIMEOUT_S)
        except Exception:
            logger.debug("Send failed for user %s", self.user_id, exc_info=True)
            await self.close(CLOSE_INTERNAL, "send failed")
            return False
        return True

    async def close(self, code: int, reason: str = "") -> None:
        if self.closed:
            return
        self.closed = True
        await safe_close(self.websocket, code, reason)
