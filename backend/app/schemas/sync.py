from pydantic import BaseModel

from app.schemas.message import MessageOut


class ReceiptStateOut(BaseModel):
    conversation_id: str
    user_id: str
    delivered_seq: int
    read_seq: int


class SyncResultOut(BaseModel):
    messages: list[MessageOut]  # ascending by seq within each conversation
    receipts: list[ReceiptStateOut]  # every active member's cursors, for status recomputation
    # Conversations with more missed messages than one sync can carry: page via REST after_seq.
    truncated: list[str]
