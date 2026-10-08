from fastapi import APIRouter, Response, status

from app.api.deps import ContactServiceDep, CurrentUserDep
from app.schemas.contact import ContactCreate, ContactOut

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("", response_model=list[ContactOut])
async def list_contacts(user: CurrentUserDep, service: ContactServiceDep) -> list[ContactOut]:
    return await service.list_for(user)


@router.post("", response_model=ContactOut, status_code=status.HTTP_201_CREATED)
async def add_contact(
    body: ContactCreate, user: CurrentUserDep, service: ContactServiceDep
) -> ContactOut:
    return await service.add(user, body)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_contact(
    contact_id: str, user: CurrentUserDep, service: ContactServiceDep
) -> Response:
    await service.remove(user, contact_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
