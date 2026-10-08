import logging

from app.models import User
from app.realtime.context import RealtimeRuntime
from app.services.factory import build_presence_service, build_receipt_service

logger = logging.getLogger(__name__)


async def load_peers(runtime: RealtimeRuntime, user_id: str) -> list[str]:
    try:
        async with runtime.session_factory() as db:
            return await build_presence_service(db, runtime.events).peer_ids(user_id)
    except Exception:
        logger.exception("Failed to load presence peers for %s", user_id)
        return []


async def on_connected(
    runtime: RealtimeRuntime, user: User, peers: list[str], *, first: bool
) -> None:
    """Offline->delivered, and tell peers we came online (only for the first socket)."""
    try:
        async with runtime.session_factory() as db:
            await build_receipt_service(db, runtime.events).deliver_pending(user)
        if first:
            async with runtime.session_factory() as db:
                await build_presence_service(db, runtime.events).announce_online(user, peers)
    except Exception:
        logger.exception("on_connected side effects failed for %s", user.id)


async def on_disconnected(runtime: RealtimeRuntime, user_id: str, *, last: bool) -> None:
    if not last:
        return
    runtime.typing_limiter.forget_user(user_id)
    try:
        async with runtime.session_factory() as db:
            await build_presence_service(db, runtime.events).announce_offline(user_id)
    except Exception:
        logger.exception("on_disconnected side effects failed for %s", user_id)
