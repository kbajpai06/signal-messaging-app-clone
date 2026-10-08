"""Typed WebSocket envelopes and client->server payloads."""

from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.message import SendMessageIn


class ClientEnvelope(BaseModel):
    """{ "type": "...", "id": "req-uuid", "ts": 1738000000000, "payload": {...} }"""

    model_config = ConfigDict(extra="ignore")

    type: str = Field(min_length=1, max_length=64)
    id: str | None = Field(default=None, max_length=64)  # request correlation id
    ts: int | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class AuthPayload(BaseModel):
    token: str = Field(min_length=1, max_length=4096)


class SendMessagePayload(SendMessageIn):
    """message.send: the REST send body plus the target conversation."""

    conversation_id: str


class ReceiptPayload(BaseModel):
    """message.delivered / message.read."""

    conversation_id: str
    up_to_seq: int = Field(ge=0)


class TypingPayload(BaseModel):
    conversation_id: str


class SyncPayload(BaseModel):
    """sync: the last seq the client holds per conversation."""

    cursors: dict[str, Annotated[int, Field(ge=0)]] = Field(default_factory=dict, max_length=500)
