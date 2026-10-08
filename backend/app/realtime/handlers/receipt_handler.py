from app.realtime.context import ConnectionContext
from app.schemas.ws_events import ClientEnvelope, ReceiptPayload
from app.services.factory import build_receipt_service


async def handle_delivered(ctx: ConnectionContext, envelope: ClientEnvelope) -> None:
    payload = ReceiptPayload.model_validate(envelope.payload)
    async with ctx.db() as db:
        service = build_receipt_service(db, ctx.runtime.events)
        await service.mark_delivered(ctx.user, payload.conversation_id, payload.up_to_seq)


async def handle_read(ctx: ConnectionContext, envelope: ClientEnvelope) -> None:
    payload = ReceiptPayload.model_validate(envelope.payload)
    async with ctx.db() as db:
        service = build_receipt_service(db, ctx.runtime.events)
        await service.mark_read(ctx.user, payload.conversation_id, payload.up_to_seq)


HANDLERS = {"message.delivered": handle_delivered, "message.read": handle_read}
