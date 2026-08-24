from fastapi import APIRouter

from app.auth.dependencies import AccessPayloadDep, AuthServiceDep, CurrentUserDep
from app.auth.schemas import AuthUserResponse, LoginRequest, RefreshTokenRequest, TokenResponse
from app.common.responses import APIResponse, success_response

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    summary="Login",
    description="Authenticate with email and password. Returns JWT access and refresh tokens.",
    response_model=APIResponse[TokenResponse],
)
async def login(payload: LoginRequest, service: AuthServiceDep) -> APIResponse[TokenResponse]:
    tokens = await service.login(payload)
    return success_response(tokens, message="Login successful")


@router.post(
    "/logout",
    summary="Logout",
    description="Revoke all refresh tokens for the authenticated user.",
    response_model=APIResponse[None],
)
async def logout(payload: AccessPayloadDep, service: AuthServiceDep) -> APIResponse[None]:
    await service.logout(payload.sub)
    return success_response(message="Logout successful")


@router.post(
    "/refresh-token",
    summary="Refresh token",
    description="Rotate a valid refresh token and issue a new access/refresh pair.",
    response_model=APIResponse[TokenResponse],
)
async def refresh_token(
    payload: RefreshTokenRequest,
    service: AuthServiceDep,
) -> APIResponse[TokenResponse]:
    tokens = await service.refresh(payload.refresh_token)
    return success_response(tokens, message="Token refreshed")


@router.get(
    "/me",
    summary="Current user",
    description="Return the authenticated user profile with roles loaded from the database.",
    response_model=APIResponse[AuthUserResponse],
)
async def me(
    current_user: CurrentUserDep,
    service: AuthServiceDep,
) -> APIResponse[AuthUserResponse]:
    profile = await service.get_me(current_user.id)
    return success_response(profile)
