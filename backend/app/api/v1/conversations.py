from typing import Annotated

from fastapi import APIRouter, File, Query, Response, UploadFile, status

from app.api.deps import (
    ConversationServiceDep,
    CurrentUserDep,
    GroupServiceDep,
    SettingsDep,
)
from app.schemas.conversation import (
    ConversationDetailOut,
    ConversationListItemOut,
    ConversationUpdateIn,
    DirectConversationIn,
    GroupCreateIn,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationListItemOut])
async def list_conversations(
    user: CurrentUserDep,
    service: ConversationServiceDep,
    q: Annotated[str | None, Query(max_length=64)] = None,
) -> list[ConversationListItemOut]:
    return await service.list_for_user(user, q)


@router.post("/direct", response_model=ConversationDetailOut)
async def open_direct_conversation(
    body: DirectConversationIn,
    response: Response,
    user: CurrentUserDep,
    service: ConversationServiceDep,
) -> ConversationDetailOut:
    detail, created = await service.get_or_create_direct(user, body.user_id)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return detail


@router.post("/group", response_model=ConversationDetailOut, status_code=status.HTTP_201_CREATED)
async def create_group(
    body: GroupCreateIn, user: CurrentUserDep, service: GroupServiceDep
) -> ConversationDetailOut:
    return await service.create_group(
        user, name=body.name, member_ids=body.member_ids, description=body.description
    )


@router.get("/{conversation_id}", response_model=ConversationDetailOut)
async def get_conversation(
    conversation_id: str, user: CurrentUserDep, service: ConversationServiceDep
) -> ConversationDetailOut:
    return await service.get_detail(user, conversation_id)


@router.patch("/{conversation_id}", response_model=ConversationDetailOut)
async def update_conversation(
    conversation_id: str,
    body: ConversationUpdateIn,
    user: CurrentUserDep,
    service: ConversationServiceDep,
) -> ConversationDetailOut:
    return await service.update(user, conversation_id, body.model_dump(exclude_unset=True))


@router.post("/{conversation_id}/avatar", response_model=ConversationDetailOut)
async def upload_group_avatar(
    conversation_id: str,
    file: Annotated[UploadFile, File()],
    user: CurrentUserDep,
    service: GroupServiceDep,
    settings: SettingsDep,
) -> ConversationDetailOut:
    data = await file.read(settings.max_upload_bytes + 1)
    return await service.set_avatar(user, conversation_id, data)
