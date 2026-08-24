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

CUSTOMER_BODY = {
    "name": "Meera Patel",
    "phone": "9876510001",
    "email": "meera@example.com",
    "notes": "Prefers morning slots",
}


@pytest.fixture
async def customers_client() -> AsyncGenerator[AsyncClient, None]:
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


async def test_admin_and_receptionist_can_create_search_view_and_update(
    customers_client: AsyncClient,
) -> None:
    headers = _headers(RoleName.ADMIN)
    created = await customers_client.post("/api/v1/customers", json=CUSTOMER_BODY, headers=headers)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["success"] is True
    customer_id = body["data"]["id"]
    assert body["data"]["visit_count"] == 0
    assert body["data"]["total_spent"] == "0.00"
    assert body["data"]["last_visit"] is None

    listed = await customers_client.get(
        "/api/v1/customers",
        params={"search": "Meera"},
        headers=_headers(RoleName.RECEPTIONIST),
    )
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 1

    profile = await customers_client.get(
        f"/api/v1/customers/{customer_id}",
        headers=_headers(RoleName.RECEPTIONIST),
    )
    assert profile.status_code == 200
    assert profile.json()["data"]["phone"] == "9876510001"
    assert profile.json()["data"]["visit_count"] == 0

    updated = await customers_client.put(
        f"/api/v1/customers/{customer_id}",
        json={"notes": "Color-treated hair"},
        headers=_headers(RoleName.RECEPTIONIST),
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["notes"] == "Color-treated hair"


async def test_staff_is_denied_customer_access(customers_client: AsyncClient) -> None:
    created = await customers_client.post(
        "/api/v1/customers",
        json=CUSTOMER_BODY,
        headers=_headers(RoleName.ADMIN),
    )
    assert created.status_code == 201
    customer_id = created.json()["data"]["id"]

    listed = await customers_client.get("/api/v1/customers", headers=_headers(RoleName.STAFF))
    assert listed.status_code == 403

    profile = await customers_client.get(
        f"/api/v1/customers/{customer_id}",
        headers=_headers(RoleName.STAFF),
    )
    assert profile.status_code == 403

    staff_create = await customers_client.post(
        "/api/v1/customers",
        json={**CUSTOMER_BODY, "phone": "9876510002"},
        headers=_headers(RoleName.STAFF),
    )
    assert staff_create.status_code == 403


async def test_unauthenticated_list_is_rejected(customers_client: AsyncClient) -> None:
    response = await customers_client.get("/api/v1/customers")
    assert response.status_code == 401


async def test_invalid_phone_is_rejected(customers_client: AsyncClient) -> None:
    response = await customers_client.post(
        "/api/v1/customers",
        json={**CUSTOMER_BODY, "phone": "123"},
        headers=_headers(RoleName.ADMIN),
    )
    assert response.status_code == 422
    assert response.json()["success"] is False


async def test_visit_fields_cannot_be_set_on_write(customers_client: AsyncClient) -> None:
    response = await customers_client.post(
        "/api/v1/customers",
        json={**CUSTOMER_BODY, "visit_count": 5},
        headers=_headers(RoleName.ADMIN),
    )
    assert response.status_code == 422
