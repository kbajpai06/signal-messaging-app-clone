import time


def now_ms() -> int:
    """Current UTC time as epoch milliseconds (the single time format used in the DB)."""
    return time.time_ns() // 1_000_000
