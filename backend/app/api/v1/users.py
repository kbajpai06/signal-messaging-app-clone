from typing import Annotated

from fastapi import APIRouter, File, Query, UploadFile

from app.api.deps import CurrentUserDep, SettingsDep, UserServiceDep
from app.schemas.user import UserDirectoryEntry, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.put("/me", response_model=UserOut)
async def update_me(body: UserUpdate, user: CurrentUserDep, service: UserServiceDep) -> UserOut:
    updated = await service.update_profile(user, body.model_dump(exclude_unset=True))
    return UserOut.model_validate(updated)


@router.post("/me/avatar", response_model=UserOut)
async def upload_avatar(
    file: Annotated[UploadFile, File()],
    user: CurrentUserDep,
    service: UserServiceDep,
    settings: SettingsDep,
) -> UserOut:
    data = await file.read(settings.max_upload_bytes + 1)
    updated = await service.set_avatar(user, data)
    return UserOut.model_validate(updated)


@router.get("/search", response_model=list[UserDirectoryEntry])
async def search_users(
    user: CurrentUserDep,
    service: UserServiceDep,
    q: Annotated[str, Query(min_length=1, max_length=64)],
) -> list[UserDirectoryEntry]:
    return await service.search(user, q)
