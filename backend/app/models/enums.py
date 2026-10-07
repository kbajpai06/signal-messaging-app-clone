from enum import StrEnum


class ConversationType(StrEnum):
    DIRECT = "direct"
    GROUP = "group"


class MemberRole(StrEnum):
    ADMIN = "admin"
    MEMBER = "member"


class MessageType(StrEnum):
    TEXT = "text"
    SYSTEM = "system"
    IMAGE = "image"
    FILE = "file"


def sql_in(column: str, enum: type[StrEnum]) -> str:
    """Build a CHECK expression so the DB constraint can never drift from the enum."""
    values = ", ".join(f"'{member.value}'" for member in enum)
    return f"{column} IN ({values})"
