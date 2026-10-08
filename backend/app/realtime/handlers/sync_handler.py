from app.realtime.context import ConnectionContext
from app.schemas.ws_events import ClientEnvelope, SyncPayload
from app.services.factory import build_sync_service


async def handle_sync(ctx: ConnectionContext, envelope: ClientEnvelope) -> None:
    payload = SyncPayload.model_validate(envelope.payload)
    async with ctx.db() as db:
        result = await build_sync_service(db).catch_up(ctx.user, payload.cursors)
    await ctx.reply(envelope, "sync.result", result.model_dump(mode="json"))


HANDLERS = {"sync": handle_sync}
