"""Wire format: envelope building/parsing and close codes."""

import json
from typing import Any

from pydantic import ValidationError

from app.schemas.ws_events import ClientEnvelope
from app.utils.time import now_ms

CLOSE_UNSUPPORTED = 1003
CLOSE_TOO_LARGE = 1009
CLOSE_INTERNAL = 1011
CLOSE_GOING_AWAY = 1001
CLOSE_UNAUTHENTICATED = 4401
CLOSE_FORBIDDEN = 4403
CLOSE_IDLE = 4408

MAX_FRAME_BYTES = 64 * 1024


class ProtocolError(Exception):
    """A malformed frame. If close_code is set, the connection must be closed."""

    def __init__(self, code: str, message: str, *, close_code: int | None = None) -> None:
        self.code = code
        self.message = message
        self.close_code = close_code
        super().__init__(message)


def server_frame(
    event_type: str, payload: dict[str, Any], *, reply_to: str | None = None
) -> dict[str, Any]:
    frame: dict[str, Any] = {"type": event_type, "ts": now_ms(), "payload": payload}
    if reply_to:
        frame["reply_to"] = reply_to
    return frame


def error_frame(reply_to: str | None, code: str, message: str) -> dict[str, Any]:
    payload = {"reply_to": reply_to, "code": code, "message": message}
    return server_frame("error", payload, reply_to=reply_to)


def encode_frame(frame: dict[str, Any]) -> str:
    return json.dumps(frame, separators=(",", ":"), ensure_ascii=False, default=str)


def parse_client_frame(text: str) -> ClientEnvelope:
    if len(text.encode("utf-8")) > MAX_FRAME_BYTES:
        raise ProtocolError(
            "frame_too_large", "Frame exceeds the size limit", close_code=CLOSE_TOO_LARGE
        )
    try:
        raw = json.loads(text)
    except ValueError as exc:
        raise ProtocolError("invalid_frame", "Frame is not valid JSON") from exc
    if not isinstance(raw, dict):
        raise ProtocolError("invalid_frame", "Frame must be a JSON object")
    try:
        return ClientEnvelope.model_validate(raw)
    except ValidationError as exc:
        raise ProtocolError("invalid_frame", "Malformed envelope") from exc
