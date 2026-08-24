from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import TokenType
from app.common.pagination import PaginationParams
from app.core.exceptions import UnauthorizedException
from app.core.security import CurrentUser, decode_token
from app.database.session import get_db

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedException("Authentication required")
    payload = decode_token(credentials.credentials, expected_type=TokenType.ACCESS)
    return CurrentUser(id=payload.sub, roles=payload.roles, email=payload.email)


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser | None:
    if credentials is None:
        return None
    return await get_current_user(credentials)


SessionDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
OptionalUserDep = Annotated[CurrentUser | None, Depends(get_current_user_optional)]
PaginationDep = Annotated[PaginationParams, Depends()]
