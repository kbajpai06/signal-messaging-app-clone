from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    phone_number: str
    username: str | None
    display_name: str
    about: str | None
    avatar_url: str | None
    avatar_color: str
    last_seen_at: int | None
    created_at: int


class UserUpdate(BaseModel):
    """PUT /users/me. Only fields present in the body are changed."""

    display_name: str | None = Field(default=None, min_length=1, max_length=64)
    about: str | None = Field(default=None, max_length=140)
    username: str | None = Field(default=None, pattern=r"^[a-z_][a-z0-9_.]{2,31}$")

    @field_validator("display_name", mode="before")
    @classmethod
    def _strip_display_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("about", mode="before")
    @classmethod
    def _blank_about_to_none(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator("username", mode="before")
    @classmethod
    def _normalize_username(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip().lower()
            return value or None
        return value

    @model_validator(mode="after")
    def _display_name_cannot_be_cleared(self) -> Self:
        if "display_name" in self.model_fields_set and self.display_name is None:
            raise ValueError("display_name cannot be null")
        return self
