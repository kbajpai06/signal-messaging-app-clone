from typing import Annotated

from fastapi import APIRouter, Header, Response, status

from app.api.deps import AuthContextDep, AuthServiceDep, CurrentUserDep, GatewayDep
from app.schemas.auth import AuthOut, OtpRequestIn, OtpRequestOut, OtpVerifyIn
from app.schemas.user import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/otp/request", response_model=OtpRequestOut)
async def request_otp(body: OtpRequestIn, service: AuthServiceDep) -> OtpRequestOut:
    await service.request_otp(body.phone_number)
    return OtpRequestOut()


@router.post("/otp/verify", response_model=AuthOut)
async def verify_otp(
    body: OtpVerifyIn,
    service: AuthServiceDep,
    user_agent: Annotated[str | None, Header()] = None,
) -> AuthOut:
    device_label = body.device_label or (user_agent[:80] if user_agent else None)
    result = await service.verify_otp(
        phone_number=body.phone_number, code=body.code, device_label=device_label
    )
    return AuthOut(
        token=result.token,
        expires_at=result.expires_at,
        user=UserOut.model_validate(result.user),
        is_new_user=result.is_new_user,
    )


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUserDep) -> UserOut:
    return UserOut.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(context: AuthContextDep, service: AuthServiceDep, gateway: GatewayDep) -> Response:
    await service.logout(context.session_id)
    await gateway.close_session(context.session_id)  # drop this session's live sockets
    return Response(status_code=status.HTTP_204_NO_CONTENT)
