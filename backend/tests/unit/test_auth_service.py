from collections.abc import AsyncGenerator
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.repository import AuthRepository
from app.auth.schemas import LoginRequest
from app.auth.service import AuthService, extract_roles, hash_refresh_token
from app.common.enums import Role as RoleName
from app.core.exceptions import UnauthorizedException
from app.core.security import hash_password
from app.database import models as _models  # noqa: F401
from app.database.base import Base
from app.users.models import Role, User, UserRole


@pytest.fixture
async def auth_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as session:
        yield session
    await engine.dispose()


async def _ensure_roles(session: AsyncSession) -> dict[RoleName, Role]:
    roles: dict[RoleName, Role] = {}
    for name in RoleName:
        role = Role(name=name)
        session.add(role)
        await session.flush()
        roles[name] = role
    return roles


async def _create_user(
    session: AsyncSession,
    *,
    email: str = "admin@example.com",
    password: str = "AdminPass123!",
    name: str = "Salon Admin",
    is_active: bool = True,
    roles: list[RoleName] | None = None,
) -> User:
    role_rows = await _ensure_roles(session)
    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        is_active=is_active,
    )
    session.add(user)
    await session.flush()
    for role_name in roles or [RoleName.ADMIN]:
        session.add(UserRole(user_id=user.id, role_id=role_rows[role_name].id))
    await session.flush()
    return user


def _service(session: AsyncSession) -> AuthService:
    return AuthService(AuthRepository(session))


async def test_login_returns_tokens_and_user(auth_session: AsyncSession) -> None:
    await _create_user(auth_session)
    result = await _service(auth_session).login(
        LoginRequest(email="admin@example.com", password="AdminPass123!")
    )
    assert result.user.email == "admin@example.com"
    assert result.user.roles == [RoleName.ADMIN]
    assert result.access_token
    assert result.refresh_token
    assert result.access_token != result.refresh_token


async def test_login_rejects_unknown_email(auth_session: AsyncSession) -> None:
    await _create_user(auth_session)
    with pytest.raises(UnauthorizedException, match="Invalid email or password"):
        await _service(auth_session).login(
            LoginRequest(email="missing@example.com", password="AdminPass123!")
        )


async def test_login_rejects_wrong_password(auth_session: AsyncSession) -> None:
    await _create_user(auth_session)
    with pytest.raises(UnauthorizedException, match="Invalid email or password"):
        await _service(auth_session).login(
            LoginRequest(email="admin@example.com", password="WrongPass123!")
        )


async def test_login_rejects_disabled_account(auth_session: AsyncSession) -> None:
    await _create_user(auth_session, is_active=False)
    with pytest.raises(UnauthorizedException, match="Account is disabled"):
        await _service(auth_session).login(
            LoginRequest(email="admin@example.com", password="AdminPass123!")
        )


async def test_refresh_rotates_token_and_rejects_reuse(auth_session: AsyncSession) -> None:
    await _create_user(auth_session)
    service = _service(auth_session)
    first = await service.login(LoginRequest(email="admin@example.com", password="AdminPass123!"))
    second = await service.refresh(first.refresh_token)
    assert second.refresh_token != first.refresh_token
    assert second.access_token != first.access_token

    with pytest.raises(UnauthorizedException, match="already been used"):
        await service.refresh(first.refresh_token)


async def test_logout_revokes_refresh_tokens(auth_session: AsyncSession) -> None:
    user = await _create_user(auth_session)
    service = _service(auth_session)
    tokens = await service.login(LoginRequest(email="admin@example.com", password="AdminPass123!"))
    await service.logout(user.id)
    with pytest.raises(UnauthorizedException, match="already been used"):
        await service.refresh(tokens.refresh_token)


async def test_get_me_returns_profile(auth_session: AsyncSession) -> None:
    user = await _create_user(auth_session, roles=[RoleName.ADMIN, RoleName.STAFF])
    loaded = await AuthRepository(auth_session).get_user_by_id(user.id)
    assert loaded is not None
    assert set(extract_roles(loaded)) == {RoleName.ADMIN, RoleName.STAFF}
    profile = await _service(auth_session).get_me(user.id)
    assert profile.id == user.id
    assert profile.name == "Salon Admin"


async def test_get_me_rejects_unknown_user(auth_session: AsyncSession) -> None:
    with pytest.raises(UnauthorizedException):
        await _service(auth_session).get_me(UUID("00000000-0000-0000-0000-000000000001"))


def test_refresh_token_hash_is_not_reversible() -> None:
    token = "plain-refresh-token"
    hashed = hash_refresh_token(token)
    assert hashed != token
    assert hash_refresh_token(token) == hashed
    assert len(hashed) == 64
