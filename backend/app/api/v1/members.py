from fastapi import APIRouter, Response, status

from app.api.deps import CurrentUserDep, GroupServiceDep
from app.models.enums import MemberRole
from app.schemas.conversation import AddMembersIn, ConversationDetailOut, MemberRoleIn

router = APIRouter(prefix="/conversations/{conversation_id}", tags=["groups"])


@router.post("/members", response_model=ConversationDetailOut)
async def add_members(
    conversation_id: str, body: AddMembersIn, user: CurrentUserDep, service: GroupServiceDep
) -> ConversationDetailOut:
    return await service.add_members(user, conversation_id, body.user_ids)


@router.delete("/members/{user_id}", response_model=ConversationDetailOut)
async def remove_member(
    conversation_id: str, user_id: str, user: CurrentUserDep, service: GroupServiceDep
) -> ConversationDetailOut:
    return await service.remove_member(user, conversation_id, user_id)


@router.patch("/members/{user_id}", response_model=ConversationDetailOut)
async def change_member_role(
    conversation_id: str,
    user_id: str,
    body: MemberRoleIn,
    user: CurrentUserDep,
    service: GroupServiceDep,
) -> ConversationDetailOut:
    return await service.change_role(user, conversation_id, user_id, MemberRole(body.role))


@router.post("/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_group(
    conversation_id: str, user: CurrentUserDep, service: GroupServiceDep
) -> Response:
    await service.leave(user, conversation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
