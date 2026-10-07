from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

from app.schemas.common import PhoneNumber
from app.schemas.user import UserOut


class OtpRequestIn(BaseModel):
    phone_number: PhoneNumber


class OtpRequestOut(BaseModel):
    sent: bool = True
    expires_in_s: int = 300


class OtpVerifyIn(BaseModel):
    phone_number: PhoneNumber
    code: Annotated[str, StringConstraints(pattern=r"^[0-9]{4,8}$")]
    device_label: str | None = Field(default=None, max_length=80)


class AuthOut(BaseModel):
    token: str
    token_type: Literal["bearer"] = "bearer"
    expires_at: int
    user: UserOut
    is_new_user: bool
