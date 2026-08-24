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
async def schedules_client() -> AsyncGenerator[AsyncClient, None]:
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


async def _create_staff(client: AsyncClient) -> str:
    response = await client.post("/api/v1/staff", json=STAFF_BODY, headers=_headers(RoleName.ADMIN))
    assert response.status_code == 201, response.text
    return response.json()["data"]["id"]


async def test_admin_and_receptionist_manage_hours_and_availability(
    schedules_client: AsyncClient,
) -> None:
    staff_id = await _create_staff(schedules_client)
    reception = _headers(RoleName.RECEPTIONIST)
    created = await schedules_client.post(
        "/api/v1/staff-schedules",
        json={
            "staff_id": staff_id,
            "day_of_week": 0,
            "start_time": "10:00:00",
            "end_time": "13:00:00",
        },
        headers=reception,
    )
    assert created.status_code == 201, created.text
    schedule_id = created.json()["data"]["id"]

    listed = await schedules_client.get(
        "/api/v1/staff-schedules",
        params={"staff_id": staff_id},
        headers=reception,
    )
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 1

    weekly = await schedules_client.put(
        f"/api/v1/staff-schedules/weekly/{staff_id}",
        json={
            "windows": [
                {
                    "day_of_week": 0,
                    "start_time": "09:00:00",
                    "end_time": "12:00:00",
                }
            ]
        },
        headers=_headers(RoleName.ADMIN),
    )
    assert weekly.status_code == 200
    assert len(weekly.json()["data"]["windows"]) == 1

    slots = await schedules_client.get(
        "/api/v1/availability",
        params={"staff_id": staff_id, "date": "2026-08-24", "duration_minutes": 30},
        headers=reception,
    )
    assert slots.status_code == 200, slots.text
    assert slots.json()["data"]["slots"][0]["start_time"] == "09:00:00"

    updated = await schedules_client.put(
        f"/api/v1/staff-schedules/{schedule_id}",
        json={"end_time": "14:00:00"},
        headers=reception,
    )
    # original window was replaced by weekly PUT, so the old id is gone
    assert updated.status_code == 404

    current_id = weekly.json()["data"]["windows"][0]["id"]
    deleted = await schedules_client.delete(
        f"/api/v1/staff-schedules/{current_id}",
        headers=_headers(RoleName.ADMIN),
    )
    assert deleted.status_code == 200


async def test_staff_is_denied_schedule_access(schedules_client: AsyncClient) -> None:
    staff_id = await _create_staff(schedules_client)
    listed = await schedules_client.get(
        "/api/v1/staff-schedules",
        headers=_headers(RoleName.STAFF),
    )
    assert listed.status_code == 403

    availability = await schedules_client.get(
        "/api/v1/availability",
        params={"staff_id": staff_id, "date": "2026-08-24", "duration_minutes": 30},
        headers=_headers(RoleName.STAFF),
    )
    assert availability.status_code == 403


async def test_unauthenticated_list_is_rejected(schedules_client: AsyncClient) -> None:
    response = await schedules_client.get("/api/v1/staff-schedules")
    assert response.status_code == 401


async def test_invalid_window_is_rejected(schedules_client: AsyncClient) -> None:
    staff_id = await _create_staff(schedules_client)
    response = await schedules_client.post(
        "/api/v1/staff-schedules",
        json={
            "staff_id": staff_id,
            "day_of_week": 0,
            "start_time": "13:00:00",
            "end_time": "10:00:00",
        },
        headers=_headers(RoleName.ADMIN),
    )
    assert response.status_code == 422
