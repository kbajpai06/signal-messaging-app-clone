from app.realtime.context import ConnectionContext
from app.schemas.ws_events import ClientEnvelope, TypingPayload
from app.services.factory import build_typing_service


async def _relay(ctx: ConnectionContext, envelope: ClientEnvelope, *, is_typing: bool) -> None:
    payload = TypingPayload.model_validate(envelope.payload)
    # Rate-limit "start" only; "stop" must always get through.
    if is_typing and not ctx.runtime.typing_limiter.allow(ctx.user_id, payload.conversation_id):
        return
    async with ctx.db() as db:
        service = build_typing_service(db, ctx.runtime.events)
        await service.relay(ctx.user, payload.conversation_id, is_typing=is_typing)


async def handle_typing_start(ctx: ConnectionContext, envelope: ClientEnvelope) -> None:
    await _relay(ctx, envelope, is_typing=True)


async def handle_typing_stop(ctx: ConnectionContext, envelope: ClientEnvelope) -> None:
    await _relay(ctx, envelope, is_typing=False)


HANDLERS = {"typing.start": handle_typing_start, "typing.stop": handle_typing_stop}
