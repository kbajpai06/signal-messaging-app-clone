import uuid


def new_id() -> str:
    return str(uuid.uuid4())


def direct_key(user_a: str, user_b: str) -> str:
    """Order-independent key that makes direct-conversation get-or-create atomic."""
    low, high = sorted((user_a, user_b))
    return f"{low}:{high}"
