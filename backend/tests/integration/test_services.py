from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.common.enums import Role as RoleName
from app.core.security import create_access_token
from app.database import models as _models  # noqa: F401
from app.database.base import Base
from app.database.session import get_db
from app.main import create_app

SERVICE_BODY = {
    "name": "Hair Cut",
    "description": "Classic haircut with wash and finish",
    "category": "Hair",
    "duration_minutes": 30,
    "price": "400.00",
}


@pytest.fixture
async def services_client() -> AsyncGenerator[AsyncClient, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

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


def _headers(role: RoleName) -> dict[str, str]:
    token = create_access_token(
        subject=uuid4(),
        roles=[role],
        email=f"{role.value.lower()}@example.com",
    )
    return {"Authorization": f"Bearer {token}"}


async def test_admin_can_create_list_update_and_deactivate(services_client: AsyncClient) -> None:
    headers = _headers(RoleName.ADMIN)
    created = await services_client.post("/api/v1/services", json=SERVICE_BODY, headers=headers)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["success"] is True
    service_id = body["data"]["id"]
    assert body["data"]["name"] == "Hair Cut"
    assert body["data"]["is_active"] is True

    listed = await services_client.get("/api/v1/services", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 1

    updated = await services_client.put(
        f"/api/v1/services/{service_id}",
        json={"price": "450.00"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["price"] == "450.00"

    deleted = await services_client.delete(f"/api/v1/services/{service_id}", headers=headers)
    assert deleted.status_code == 200

    active = await services_client.get(
        "/api/v1/services",
        params={"is_active": True},
        headers=headers,
    )
    assert active.json()["data"]["total"] == 0

    hidden = await services_client.get(
        "/api/v1/services",
        params={"is_active": False},
        headers=headers,
    )
    assert hidden.json()["data"]["total"] == 1
    assert hidden.json()["data"]["items"][0]["is_active"] is False


async def test_receptionist_and_staff_can_list_but_not_write(services_client: AsyncClient) -> None:
    admin_create = await services_client.post(
        "/api/v1/services",
        json=SERVICE_BODY,
        headers=_headers(RoleName.ADMIN),
    )
    assert admin_create.status_code == 201
    service_id = admin_create.json()["data"]["id"]

    listed = await services_client.get("/api/v1/services", headers=_headers(RoleName.RECEPTIONIST))
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 1

    staff_list = await services_client.get("/api/v1/services", headers=_headers(RoleName.STAFF))
    assert staff_list.status_code == 200

    staff_create = await services_client.post(
        "/api/v1/services",
        json={**SERVICE_BODY, "name": "Facial"},
        headers=_headers(RoleName.STAFF),
    )
    assert staff_create.status_code == 403

    reception_update = await services_client.put(
        f"/api/v1/services/{service_id}",
        json={"price": "500.00"},
        headers=_headers(RoleName.RECEPTIONIST),
    )
    assert reception_update.status_code == 403

    staff_delete = await services_client.delete(
        f"/api/v1/services/{service_id}",
        headers=_headers(RoleName.STAFF),
    )
    assert staff_delete.status_code == 403


async def test_unauthenticated_list_is_rejected(services_client: AsyncClient) -> None:
    response = await services_client.get("/api/v1/services")
    assert response.status_code == 401


async def test_invalid_price_and_duration_are_rejected(services_client: AsyncClient) -> None:
    headers = _headers(RoleName.ADMIN)
    zero_price = await services_client.post(
        "/api/v1/services",
        json={**SERVICE_BODY, "price": "0"},
        headers=headers,
    )
    assert zero_price.status_code == 422

    bad_duration = await services_client.post(
        "/api/v1/services",
        json={**SERVICE_BODY, "name": "Spa", "duration_minutes": 0},
        headers=headers,
    )
    assert bad_duration.status_code == 422
    assert bad_duration.json()["success"] is False
