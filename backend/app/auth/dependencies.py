from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials

from app.auth.repository import AuthRepository
from app.auth.service import AuthService, extract_roles
from app.common.dependencies import SessionDep, bearer_scheme
from app.common.enums import TokenType
from app.core.exceptions import UnauthorizedException
from app.core.security import CurrentUser, TokenPayload, decode_token


async def get_access_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> TokenPayload:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedException("Authentication required")
    return decode_token(credentials.credentials, expected_type=TokenType.ACCESS)


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(AuthRepository(session))


async def get_current_user(
    payload: Annotated[TokenPayload, Depends(get_access_payload)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> CurrentUser:
    """Active, non-deleted user loaded from the database (roles refreshed)."""
    user = await service.repository.get_user_by_id(payload.sub)
    if user is None or not user.is_active:
        raise UnauthorizedException("Authentication required")
    return CurrentUser(id=user.id, roles=extract_roles(user), email=user.email)


AccessPayloadDep = Annotated[TokenPayload, Depends(get_access_payload)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
