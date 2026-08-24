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
SERVICE_BODY = {
    "name": "Hair Cut",
    "category": "Hair",
    "duration_minutes": 30,
    "price": "400.00",
}
CUSTOMER_BODY = {"name": "Meera Patel", "phone": "9876510001"}


@pytest.fixture
async def tips_client() -> AsyncGenerator[AsyncClient, None]:
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


def _headers(role: RoleName, *, subject=None) -> dict[str, str]:
    token = create_access_token(
        subject=subject or uuid4(),
        roles=[role],
        email=f"{role.value.lower()}@example.com",
    )
    return {"Authorization": f"Bearer {token}"}


async def _seed(client: AsyncClient) -> tuple[str, str, str]:
    admin = _headers(RoleName.ADMIN)
    staff = await client.post("/api/v1/staff", json=STAFF_BODY, headers=admin)
    assert staff.status_code == 201, staff.text
    staff_id = staff.json()["data"]["id"]
    window = await client.post(
        "/api/v1/staff-schedules",
        json={
            "staff_id": staff_id,
            "day_of_week": 0,
            "start_time": "09:00:00",
            "end_time": "18:00:00",
        },
        headers=admin,
    )
    assert window.status_code == 201, window.text
    service = await client.post("/api/v1/services", json=SERVICE_BODY, headers=admin)
    assert service.status_code == 201, service.text
    customer = await client.post("/api/v1/customers", json=CUSTOMER_BODY, headers=admin)
    assert customer.status_code == 201, customer.text
    return staff_id, customer.json()["data"]["id"], service.json()["data"]["id"]


async def _book(client: AsyncClient) -> tuple[str, str, dict[str, str]]:
    staff_id, customer_id, service_id = await _seed(client)
    headers = _headers(RoleName.RECEPTIONIST)
    created = await client.post(
        "/api/v1/appointments",
        json={
            "customer_id": customer_id,
            "staff_id": staff_id,
            "appointment_date": "2026-08-24",
            "start_time": "10:00:00",
            "service_ids": [service_id],
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    return created.json()["data"]["id"], staff_id, headers


async def test_receptionist_can_add_edit_and_list_tips(tips_client: AsyncClient) -> None:
    appointment_id, staff_id, headers = await _book(tips_client)
    created = await tips_client.post(
        "/api/v1/tips",
        json={
            "appointment_id": appointment_id,
            "amount": "100.00",
            "notes": "Cash tip",
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    body = created.json()["data"]
    tip_id = body["id"]
    assert body["amount"] == "100.00"
    assert body["staff_id"] == staff_id
    assert body["notes"] == "Cash tip"

    extra = await tips_client.post(
        "/api/v1/tips",
        json={"appointment_id": appointment_id, "amount": "25.00"},
        headers=headers,
    )
    assert extra.status_code == 201, extra.text

    updated = await tips_client.put(
        f"/api/v1/tips/{tip_id}",
        json={"amount": "120.00"},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["data"]["amount"] == "120.00"

    listed = await tips_client.get(
        "/api/v1/tips",
        params={"appointment_id": appointment_id},
        headers=headers,
    )
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 2

    by_staff = await tips_client.get(f"/api/v1/tips/staff/{staff_id}", headers=headers)
    assert by_staff.status_code == 200
    assert by_staff.json()["data"]["total"] == 2

    detail = await tips_client.get(f"/api/v1/tips/{tip_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["data"]["amount"] == "120.00"


async def test_staff_cannot_write_tips(tips_client: AsyncClient) -> None:
    appointment_id, _staff_id, _headers_desk = await _book(tips_client)
    staff = _headers(RoleName.STAFF)
    created = await tips_client.post(
        "/api/v1/tips",
        json={"appointment_id": appointment_id, "amount": "50.00"},
        headers=staff,
    )
    assert created.status_code == 403
    listed = await tips_client.get("/api/v1/tips", headers=staff)
    assert listed.status_code == 403


async def test_cancelled_and_invalid_amount_are_rejected(tips_client: AsyncClient) -> None:
    appointment_id, _staff_id, headers = await _book(tips_client)
    zero = await tips_client.post(
        "/api/v1/tips",
        json={"appointment_id": appointment_id, "amount": "0"},
        headers=headers,
    )
    assert zero.status_code == 422

    cancelled = await tips_client.patch(
        f"/api/v1/appointments/{appointment_id}/cancel",
        headers=headers,
    )
    assert cancelled.status_code == 200
    blocked = await tips_client.post(
        "/api/v1/tips",
        json={"appointment_id": appointment_id, "amount": "50.00"},
        headers=headers,
    )
    assert blocked.status_code == 409


async def test_unauthenticated_list_is_rejected(tips_client: AsyncClient) -> None:
    response = await tips_client.get("/api/v1/tips")
    assert response.status_code == 401
