from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.schemas.message import MessagePreviewOut
from app.schemas.user import UserSummary

GroupName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]
MAX_DISAPPEARING_TTL_S = 4 * 7 * 24 * 3600  # 4 weeks


def _blank_to_none(value: object) -> object:
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


class MemberOut(BaseModel):
    user: UserSummary
    role: Literal["admin", "member"]
    joined_at: int
    online: bool
    last_delivered_seq: int
    last_read_seq: int


class ConversationDetailOut(BaseModel):
    """Viewer-agnostic, so the same payload can be pushed to every member over WS."""

    id: str
    type: Literal["direct", "group"]
    name: str | None
    avatar_url: str | None
    description: str | None
    disappearing_ttl_s: int | None
    created_by: str
    created_at: int
    last_seq: int
    last_message_at: int
    members: list[MemberOut]


class ConversationListItemOut(ConversationDetailOut):
    last_message: MessagePreviewOut | None
    unread_count: int
    muted_until: int | None
    is_archived: bool


class DirectConversationIn(BaseModel):
    user_id: str


class GroupCreateIn(BaseModel):
    name: GroupName
    member_ids: list[str] = Field(min_length=1, max_length=99)
    description: str | None = Field(default=None, max_length=480)

    _clean_description = field_validator("description", mode="before")(_blank_to_none)


class ConversationUpdateIn(BaseModel):
    """PATCH. Only fields present in the body are changed; null clears description / TTL."""

    name: GroupName | None = None
    description: str | None = Field(default=None, max_length=480)
    disappearing_ttl_s: int | None = Field(default=None, ge=1, le=MAX_DISAPPEARING_TTL_S)

    _clean_description = field_validator("description", mode="before")(_blank_to_none)

    @model_validator(mode="after")
    def _name_cannot_be_cleared(self) -> Self:
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("name cannot be null")
        return self


class AddMembersIn(BaseModel):
    user_ids: list[str] = Field(min_length=1, max_length=50)


class MemberRoleIn(BaseModel):
    role: Literal["admin", "member"]
