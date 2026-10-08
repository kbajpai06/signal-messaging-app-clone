from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.common import PhoneNumber
from app.schemas.user import UserDirectoryEntry


class ContactCreate(BaseModel):
    user_id: str | None = None
    phone_number: PhoneNumber | None = None
    nickname: str | None = Field(default=None, max_length=64)

    @field_validator("nickname", mode="before")
    @classmethod
    def _blank_nickname_to_none(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @model_validator(mode="after")
    def _exactly_one_target(self) -> Self:
        if (self.user_id is None) == (self.phone_number is None):
            raise ValueError("Provide exactly one of user_id or phone_number")
        return self


class ContactOut(BaseModel):
    id: str
    nickname: str | None
    created_at: int
    online: bool
    user: UserDirectoryEntry
