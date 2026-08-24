from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.common.enums import Role


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class RefreshTokenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(min_length=1)


class AuthUserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    is_active: bool
    roles: list[Role]


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: AuthUserResponse
