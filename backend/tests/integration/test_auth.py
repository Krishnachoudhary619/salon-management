from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.common.enums import Role as RoleName
from app.core.security import hash_password
from app.database import models as _models  # noqa: F401
from app.database.base import Base
from app.database.session import get_db
from app.main import create_app
from app.users.models import Role, User, UserRole

LOGIN_EMAIL = "admin@example.com"
LOGIN_PASSWORD = "AdminPass123!"


@pytest.fixture
async def auth_client() -> AsyncGenerator[AsyncClient, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with session_maker() as session:
        roles: dict[RoleName, Role] = {}
        for name in RoleName:
            role = Role(name=name)
            session.add(role)
            await session.flush()
            roles[name] = role
        user = User(
            name="Salon Admin",
            email=LOGIN_EMAIL,
            password_hash=hash_password(LOGIN_PASSWORD),
            is_active=True,
        )
        session.add(user)
        await session.flush()
        session.add(UserRole(user_id=user.id, role_id=roles[RoleName.ADMIN].id))
        await session.commit()

    app = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
    await engine.dispose()


async def _login(client: AsyncClient) -> dict[str, object]:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": LOGIN_EMAIL, "password": LOGIN_PASSWORD},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert "password" not in body["data"]
    return body["data"]


async def test_login_success_envelope(auth_client: AsyncClient) -> None:
    data = await _login(auth_client)
    assert data["user"]["email"] == LOGIN_EMAIL
    assert data["user"]["roles"] == ["ADMIN"]
    assert data["access_token"]
    assert data["refresh_token"]


async def test_login_invalid_password(auth_client: AsyncClient) -> None:
    response = await auth_client.post(
        "/api/v1/auth/login",
        json={"email": LOGIN_EMAIL, "password": "nope"},
    )
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["message"] == "Invalid email or password"


async def test_me_requires_access_token(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["success"] is False


async def test_me_returns_current_user(auth_client: AsyncClient) -> None:
    data = await _login(auth_client)
    response = await auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert response.status_code == 200
    profile = response.json()["data"]
    assert profile["email"] == LOGIN_EMAIL
    assert profile["name"] == "Salon Admin"
    assert profile["roles"] == ["ADMIN"]


async def test_refresh_token_issues_new_pair(auth_client: AsyncClient) -> None:
    data = await _login(auth_client)
    response = await auth_client.post(
        "/api/v1/auth/refresh-token",
        json={"refresh_token": data["refresh_token"]},
    )
    assert response.status_code == 200
    refreshed = response.json()["data"]
    assert refreshed["refresh_token"] != data["refresh_token"]
    assert refreshed["access_token"] != data["access_token"]


async def test_refresh_rejects_access_token(auth_client: AsyncClient) -> None:
    data = await _login(auth_client)
    response = await auth_client.post(
        "/api/v1/auth/refresh-token",
        json={"refresh_token": data["access_token"]},
    )
    assert response.status_code == 401
    assert response.json()["message"] == "Invalid token type"


async def test_logout_then_refresh_fails(auth_client: AsyncClient) -> None:
    data = await _login(auth_client)
    logout = await auth_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert logout.status_code == 200
    assert logout.json()["success"] is True

    refresh = await auth_client.post(
        "/api/v1/auth/refresh-token",
        json={"refresh_token": data["refresh_token"]},
    )
    assert refresh.status_code == 401


async def test_docs_include_auth_routes(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/auth/logout" in paths
    assert "/api/v1/auth/refresh-token" in paths
    assert "/api/v1/auth/me" in paths
