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
async def appointments_client() -> AsyncGenerator[AsyncClient, None]:
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


async def test_receptionist_booking_status_reschedule_and_calendar(
    appointments_client: AsyncClient,
) -> None:
    staff_id, customer_id, service_id = await _seed(appointments_client)
    headers = _headers(RoleName.RECEPTIONIST)
    created = await appointments_client.post(
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
    body = created.json()["data"]
    appointment_id = body["id"]
    assert body["status"] == "PENDING"
    assert body["end_time"] == "10:30:00"

    listed = await appointments_client.get("/api/v1/appointments", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 1

    details = await appointments_client.get(
        f"/api/v1/appointments/{appointment_id}",
        headers=headers,
    )
    assert details.status_code == 200
    assert details.json()["data"]["customer_name"] == "Meera Patel"

    confirmed = await appointments_client.patch(
        f"/api/v1/appointments/{appointment_id}/status",
        json={"status": "CONFIRMED"},
        headers=headers,
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["data"]["status"] == "CONFIRMED"

    moved = await appointments_client.patch(
        f"/api/v1/appointments/{appointment_id}/reschedule",
        json={"appointment_date": "2026-08-24", "start_time": "11:00:00"},
        headers=headers,
    )
    assert moved.status_code == 200
    assert moved.json()["data"]["start_time"] == "11:00:00"

    calendar = await appointments_client.get(
        "/api/v1/appointments/calendar",
        params={"start_date": "2026-08-24", "end_date": "2026-08-24"},
        headers=headers,
    )
    assert calendar.status_code == 200
    assert calendar.json()["data"]["days"][0]["appointments"][0]["id"] == appointment_id

    cancelled = await appointments_client.patch(
        f"/api/v1/appointments/{appointment_id}/cancel",
        headers=headers,
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["data"]["status"] == "CANCELLED"


async def test_staff_without_profile_is_denied(appointments_client: AsyncClient) -> None:
    staff_id, customer_id, service_id = await _seed(appointments_client)
    created = await appointments_client.post(
        "/api/v1/appointments",
        json={
            "customer_id": customer_id,
            "staff_id": staff_id,
            "appointment_date": "2026-08-24",
            "start_time": "10:00:00",
            "service_ids": [service_id],
        },
        headers=_headers(RoleName.ADMIN),
    )
    assert created.status_code == 201
    listed = await appointments_client.get(
        "/api/v1/appointments",
        headers=_headers(RoleName.STAFF),
    )
    assert listed.status_code == 403


async def test_unauthenticated_list_is_rejected(appointments_client: AsyncClient) -> None:
    response = await appointments_client.get("/api/v1/appointments")
    assert response.status_code == 401


async def test_invalid_status_transition_is_rejected(appointments_client: AsyncClient) -> None:
    staff_id, customer_id, service_id = await _seed(appointments_client)
    created = await appointments_client.post(
        "/api/v1/appointments",
        json={
            "customer_id": customer_id,
            "staff_id": staff_id,
            "appointment_date": "2026-08-24",
            "start_time": "10:00:00",
            "service_ids": [service_id],
        },
        headers=_headers(RoleName.ADMIN),
    )
    appointment_id = created.json()["data"]["id"]
    skipped = await appointments_client.patch(
        f"/api/v1/appointments/{appointment_id}/status",
        json={"status": "COMPLETED"},
        headers=_headers(RoleName.ADMIN),
    )
    assert skipped.status_code == 422
