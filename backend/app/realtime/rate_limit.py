from collections.abc import Callable

from app.utils.time import now_ms

TYPING_MIN_INTERVAL_MS = 2000
_MAX_KEYS_PER_USER = 512


class MinIntervalLimiter:
    """Allow at most one event per (user, key) every `interval_ms`."""

    def __init__(self, interval_ms: int, clock: Callable[[], int] = now_ms) -> None:
        self._interval_ms = interval_ms
        self._clock = clock
        self._last: dict[str, dict[str, int]] = {}

    def allow(self, user_id: str, key: str) -> bool:
        now = self._clock()
        per_user = self._last.setdefault(user_id, {})
        if len(per_user) > _MAX_KEYS_PER_USER:  # bound memory against junk keys
            per_user.clear()
        last = per_user.get(key)
        if last is not None and now - last < self._interval_ms:
            return False
        per_user[key] = now
        return True

    def forget_user(self, user_id: str) -> None:
        self._last.pop(user_id, None)
