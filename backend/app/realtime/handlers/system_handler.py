from app.realtime.context import ConnectionContext
from app.schemas.ws_events import ClientEnvelope


async def handle_ping(ctx: ConnectionContext, envelope: ClientEnvelope) -> None:
    await ctx.reply(envelope, "pong", {})


HANDLERS = {"ping": handle_ping}
