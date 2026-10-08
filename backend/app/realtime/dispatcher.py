import logging
from collections.abc import Awaitable, Callable, Mapping

from pydantic import ValidationError

from app.core.errors import AppError
from app.realtime.context import ConnectionContext
from app.schemas.ws_events import ClientEnvelope

logger = logging.getLogger(__name__)

Handler = Callable[[ConnectionContext, ClientEnvelope], Awaitable[None]]


class Dispatcher:
    """event type -> handler registry. Adding an event = adding a handler (Open/Closed)."""

    def __init__(self) -> None:
        self._handlers: dict[str, Handler] = {}

    def register_all(self, handlers: Mapping[str, Handler]) -> None:
        for event_type, handler in handlers.items():
            if event_type in self._handlers:
                raise ValueError(f"Duplicate handler for event {event_type!r}")
            self._handlers[event_type] = handler

    async def dispatch(self, ctx: ConnectionContext, envelope: ClientEnvelope) -> None:
        handler = self._handlers.get(envelope.type)
        if handler is None:
            await ctx.reply_error(envelope, "unknown_event", f"Unknown event: {envelope.type}")
            return
        try:
            await handler(ctx, envelope)
        except AppError as exc:
            await ctx.reply_error(envelope, exc.code, exc.message)
        except ValidationError as exc:
            first = exc.errors()[0]
            field = ".".join(str(part) for part in first["loc"])
            await ctx.reply_error(
                envelope, "validation_error", f"Invalid payload ({field}): {first['msg']}"
            )
        except Exception:
            logger.exception("Unhandled error in %s handler", envelope.type)
            await ctx.reply_error(envelope, "internal_error", "Something went wrong")
