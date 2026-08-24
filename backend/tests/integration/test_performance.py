from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from uuid import UUID, uuid4

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
IDLE_STAFF_BODY = {
    "name": "Amit Kumar",
    "email": "amit@example.com",
    "password": "StaffPass123!",
    "phone": "9876500002",
    "designation": "Junior Stylist",
    "commission_percentage": "20.00",
    "joining_date": "2024-06-01",
}
SERVICE_BODY = {
    "name": "Hair Cut",
    "category": "Hair",
    "duration_minutes": 30,
    "price": "400.00",
}
CUSTOMER_BODY = {"name": "Meera Patel", "phone": "9876510001"}
_WORKFLOW = ("CONFIRMED", "ARRIVED", "IN_PROGRESS", "COMPLETED")


@pytest.fixture
async def performance_client() -> AsyncGenerator[AsyncClient, None]:
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


async def _complete_paid_visit_with_tip(
    client: AsyncClient,
) -> tuple[str, str, str]:
    admin = _headers(RoleName.ADMIN)
    today = datetime.now(UTC).date()
    staff = await client.post("/api/v1/staff", json=STAFF_BODY, headers=admin)
    assert staff.status_code == 201, staff.text
    staff_id = staff.json()["data"]["id"]
    user_id = staff.json()["data"]["user_id"]
    window = await client.post(
        "/api/v1/staff-schedules",
        json={
            "staff_id": staff_id,
            "day_of_week": today.weekday(),
            "start_time": "09:00:00",
            "end_time": "18:00:00",
        },
        headers=admin,
    )
    assert window.status_code == 201, window.text
    idle = await client.post("/api/v1/staff", json=IDLE_STAFF_BODY, headers=admin)
    assert idle.status_code == 201, idle.text
    service = await client.post("/api/v1/services", json=SERVICE_BODY, headers=admin)
    assert service.status_code == 201, service.text
    customer = await client.post("/api/v1/customers", json=CUSTOMER_BODY, headers=admin)
    assert customer.status_code == 201, customer.text
    created = await client.post(
        "/api/v1/appointments",
        json={
            "customer_id": customer.json()["data"]["id"],
            "staff_id": staff_id,
            "appointment_date": today.isoformat(),
            "start_time": "10:00:00",
            "service_ids": [service.json()["data"]["id"]],
        },
        headers=admin,
    )
    assert created.status_code == 201, created.text
    appointment_id = created.json()["data"]["id"]
    for status in _WORKFLOW:
        patched = await client.patch(
            f"/api/v1/appointments/{appointment_id}/status",
            json={"status": status},
            headers=admin,
        )
        assert patched.status_code == 200, patched.text
    paid = await client.post(
        "/api/v1/payments",
        json={
            "appointment_id": appointment_id,
            "amount": "400.00",
            "payment_method": "CASH",
        },
        headers=admin,
    )
    assert paid.status_code == 201, paid.text
    tipped = await client.post(
        "/api/v1/tips",
        json={"appointment_id": appointment_id, "amount": "100.00"},
        headers=admin,
    )
    assert tipped.status_code == 201, tipped.text
    return staff_id, user_id, idle.json()["data"]["id"]


async def test_admin_team_and_staff_performance(performance_client: AsyncClient) -> None:
    staff_id, _user_id, idle_id = await _complete_paid_visit_with_tip(performance_client)
    admin = _headers(RoleName.ADMIN)
    team = await performance_client.get("/api/v1/performance/team", headers=admin)
    assert team.status_code == 200, team.text
    items = team.json()["data"]["items"]
    assert [row["staff_name"] for row in items] == ["Priya Sharma", "Amit Kumar"]
    priya = items[0]
    assert priya["staff_id"] == staff_id
    assert priya["revenue_generated"] == "400.00"
    assert priya["customers_served"] == 1
    assert priya["appointments_completed"] == 1
    assert priya["tips_earned"] == "100.00"
    assert priya["commission_earned"] == "160.00"
    idle = next(row for row in items if row["staff_id"] == idle_id)
    assert idle["revenue_generated"] == "0.00"
    assert idle["appointments_completed"] == 0

    detail = await performance_client.get(f"/api/v1/performance/staff/{staff_id}", headers=admin)
    assert detail.status_code == 200, detail.text
    card = detail.json()["data"]
    assert card["staff_name"] == "Priya Sharma"
    assert card["revenue_generated"] == "400.00"
    assert card["tips_earned"] == "100.00"
    assert card["commission_earned"] == "160.00"


async def test_staff_can_read_own_but_not_team_or_peer(
    performance_client: AsyncClient,
) -> None:
    staff_id, user_id, idle_id = await _complete_paid_visit_with_tip(performance_client)
    staff = _headers(RoleName.STAFF, subject=UUID(user_id))
    own = await performance_client.get(f"/api/v1/performance/staff/{staff_id}", headers=staff)
    assert own.status_code == 200, own.text
    assert own.json()["data"]["appointments_completed"] == 1

    peer = await performance_client.get(f"/api/v1/performance/staff/{idle_id}", headers=staff)
    assert peer.status_code == 403
    team = await performance_client.get("/api/v1/performance/team", headers=staff)
    assert team.status_code == 403


async def test_receptionist_and_anonymous_are_rejected(
    performance_client: AsyncClient,
) -> None:
    staff_id, _user_id, _idle_id = await _complete_paid_visit_with_tip(performance_client)
    desk = _headers(RoleName.RECEPTIONIST)
    team = await performance_client.get("/api/v1/performance/team", headers=desk)
    assert team.status_code == 403
    staff = await performance_client.get(
        f"/api/v1/performance/staff/{staff_id}",
        headers=desk,
    )
    assert staff.status_code == 403
    anonymous = await performance_client.get("/api/v1/performance/team")
    assert anonymous.status_code == 401


async def test_invalid_date_range_is_rejected(performance_client: AsyncClient) -> None:
    admin = _headers(RoleName.ADMIN)
    response = await performance_client.get(
        "/api/v1/performance/team",
        params={"start_date": "2026-08-24", "end_date": "2026-08-01"},
        headers=admin,
    )
    assert response.status_code == 422
