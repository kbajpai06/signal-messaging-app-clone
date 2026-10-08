import re

from app.core.config import Settings


def is_origin_allowed(origin: str | None, settings: Settings) -> bool:
    """Browsers do not apply CORS to WebSocket upgrades, so the server checks Origin itself.

    A missing Origin means a non-browser client (curl, wscat, scripts). Cross-site hijacking
    is a browser-only attack and browsers always send Origin, so those are allowed.
    """
    if origin is None:
        return True
    if origin in settings.cors_origin_list:
        return True
    pattern = settings.cors_origin_regex
    return bool(pattern and re.fullmatch(pattern, origin))
