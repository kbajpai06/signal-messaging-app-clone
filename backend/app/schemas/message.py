from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

# "sending" exists only on the client (optimistic, not yet acked).
MessageStatus = Literal["sent", "delivered", "read"]

ClientId = Annotated[
    str, StringConstraints(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
]
MessageBody = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)
]


class ReplyPreviewOut(BaseModel):
    id: str
    seq: int
    sender_id: str | None
    type: str
    body: str | None


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    seq: int
    sender_id: str | None
    client_id: str | None
    type: str
    body: str | None
    reply_to: ReplyPreviewOut | None
    created_at: int
    expires_at: int | None
    deleted_at: int | None
    # Only set on the viewer's own messages (derived from receipt cursors).
    status: MessageStatus | None


class MessagePreviewOut(BaseModel):
    """Compact last-message payload for the conversation list."""

    id: str
    seq: int
    sender_id: str | None
    type: str
    body: str | None
    created_at: int
    status: MessageStatus | None


class MessagePageOut(BaseModel):
    items: list[MessageOut]  # always ascending by seq
    has_more: bool


class SendMessageIn(BaseModel):
    client_id: ClientId
    body: MessageBody
    type: Literal["text"] = "text"
    reply_to_id: str | None = None


class ReadIn(BaseModel):
    up_to_seq: int = Field(ge=0)
