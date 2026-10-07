from fastapi import APIRouter

from app.api.deps import CurrentUserDep, UserServiceDep
from app.schemas.user import UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.put("/me", response_model=UserOut)
async def update_me(body: UserUpdate, user: CurrentUserDep, service: UserServiceDep) -> UserOut:
    updated = await service.update_profile(user, body.model_dump(exclude_unset=True))
    return UserOut.model_validate(updated)
