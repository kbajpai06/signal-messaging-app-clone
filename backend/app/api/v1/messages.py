from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.api.deps import CurrentUserDep, MessageServiceDep, ReceiptServiceDep
from app.schemas.message import MessageOut, MessagePageOut, ReadIn, SendMessageIn

router = APIRouter(prefix="/conversations/{conversation_id}", tags=["messages"])


@router.get("/messages", response_model=MessagePageOut)
async def list_messages(
    conversation_id: str,
    user: CurrentUserDep,
    service: MessageServiceDep,
    before_seq: Annotated[int | None, Query(ge=1)] = None,
    after_seq: Annotated[int | None, Query(ge=0)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
) -> MessagePageOut:
    return await service.history(
        user, conversation_id, before_seq=before_seq, after_seq=after_seq, limit=limit
    )


@router.post("/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: str,
    body: SendMessageIn,
    response: Response,
    user: CurrentUserDep,
    service: MessageServiceDep,
) -> MessageOut:
    message, created = await service.send(user, conversation_id, body)
    if not created:
        response.status_code = status.HTTP_200_OK  # idempotent replay of the same client_id
    return message


@router.post("/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(
    conversation_id: str,
    body: ReadIn,
    user: CurrentUserDep,
    service: ReceiptServiceDep,
) -> Response:
    await service.mark_read(user, conversation_id, body.up_to_seq)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
