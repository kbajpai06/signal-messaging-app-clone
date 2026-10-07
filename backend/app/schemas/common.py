import re
from typing import Annotated

from pydantic import BeforeValidator, StringConstraints


def _normalize_phone(value: object) -> object:
    if isinstance(value, str):
        return re.sub(r"[\s\-().]", "", value)
    return value


# E.164: "+" followed by 8-15 digits, first digit non-zero.
PhoneNumber = Annotated[
    str,
    BeforeValidator(_normalize_phone),
    StringConstraints(pattern=r"^\+[1-9][0-9]{7,14}$"),
]
