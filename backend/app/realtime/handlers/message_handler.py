from app.realtime.context import ConnectionContext
from app.schemas.ws_events import ClientEnvelope, SendMessagePayload
from app.services.factory import build_message_service


async def handle_message_send(ctx: ConnectionContext, envelope: ClientEnvelope) -> None:
    payload = SendMessagePayload.model_validate(envelope.payload)
    async with ctx.db() as db:
        service = build_message_service(db, ctx.runtime.events)
        # Idempotent on (sender, client_id): a retry returns the existing message.
        message, _ = await service.send(ctx.user, payload.conversation_id, payload)
    await ctx.reply(
        envelope,
        "message.ack",
        {
            "client_id": payload.client_id,
            "id": message.id,
            "conversation_id": message.conversation_id,
            "seq": message.seq,
            "created_at": message.created_at,
        },
    )


HANDLERS = {"message.send": handle_message_send}
