import hashlib

AVATAR_COLORS = (
    "#C73F0A",
    "#C2185B",
    "#8E24AA",
    "#5E35B1",
    "#3949AB",
    "#1E88E5",
    "#00897B",
    "#43A047",
    "#EF6C00",
    "#6D4C41",
)


def avatar_color_for(user_id: str) -> str:
    """Deterministic fallback avatar color derived from the user id."""
    digest = hashlib.md5(user_id.encode(), usedforsecurity=False).digest()
    return AVATAR_COLORS[digest[0] % len(AVATAR_COLORS)]
