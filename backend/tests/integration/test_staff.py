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
from app.users.models import Role

STAFF_BODY = {
    "name": "Priya Sharma",
    "email": "priya@example.com",
    "password": "StaffPass123!",
    "phone": "9876500001",
    "designation": "Senior Stylist",
    "commission_percentage": "40.00",
    "joining_date": "2024-01-15",
}


@pytest.fixture
async def staff_client() -> AsyncGenerator[AsyncClient, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with session_maker() as session:
        for name in RoleName:
            session.add(Role(name=name))
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


def _headers(role: RoleName) -> dict[str, str]:
    token = create_access_token(
        subject=uuid4(),
        roles=[role],
        email=f"{role.value.lower()}@example.com",
    )
    return {"Authorization": f"Bearer {token}"}


async def test_admin_can_create_list_view_update_and_deactivate(
    staff_client: AsyncClient,
) -> None:
    headers = _headers(RoleName.ADMIN)
    created = await staff_client.post("/api/v1/staff", json=STAFF_BODY, headers=headers)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["success"] is True
    staff_id = body["data"]["id"]
    assert "password" not in body["data"]
    assert body["data"]["phone"] == "9876500001"

    listed = await staff_client.get("/api/v1/staff", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 1

    viewed = await staff_client.get(f"/api/v1/staff/{staff_id}", headers=headers)
    assert viewed.status_code == 200
    assert viewed.json()["data"]["name"] == "Priya Sharma"

    updated = await staff_client.put(
        f"/api/v1/staff/{staff_id}",
        json={"designation": "Lead Stylist"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["designation"] == "Lead Stylist"

    deleted = await staff_client.delete(f"/api/v1/staff/{staff_id}", headers=headers)
    assert deleted.status_code == 200
    missing = await staff_client.get(f"/api/v1/staff/{staff_id}", headers=headers)
    assert missing.status_code == 404


async def test_staff_and_receptionist_are_denied(staff_client: AsyncClient) -> None:
    create_staff = await staff_client.post(
        "/api/v1/staff",
        json=STAFF_BODY,
        headers=_headers(RoleName.STAFF),
    )
    assert create_staff.status_code == 403

    list_reception = await staff_client.get(
        "/api/v1/staff",
        headers=_headers(RoleName.RECEPTIONIST),
    )
    assert list_reception.status_code == 403


async def test_unauthenticated_list_is_rejected(staff_client: AsyncClient) -> None:
    response = await staff_client.get("/api/v1/staff")
    assert response.status_code == 401


async def test_invalid_phone_is_rejected(staff_client: AsyncClient) -> None:
    response = await staff_client.post(
        "/api/v1/staff",
        json={**STAFF_BODY, "phone": "123"},
        headers=_headers(RoleName.ADMIN),
    )
    assert response.status_code == 422
    assert response.json()["success"] is False
