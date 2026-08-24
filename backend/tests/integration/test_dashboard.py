from collections.abc import AsyncGenerator
from datetime import UTC, datetime
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
_WORKFLOW = ("CONFIRMED", "ARRIVED", "IN_PROGRESS", "COMPLETED")


@pytest.fixture
async def dashboard_client() -> AsyncGenerator[AsyncClient, None]:
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


def _today() -> str:
    return datetime.now(UTC).date().isoformat()


async def _complete_paid_visit(client: AsyncClient) -> None:
    admin = _headers(RoleName.ADMIN)
    today = datetime.now(UTC).date()
    staff = await client.post("/api/v1/staff", json=STAFF_BODY, headers=admin)
    assert staff.status_code == 201, staff.text
    staff_id = staff.json()["data"]["id"]
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


async def test_admin_overview_and_charts(dashboard_client: AsyncClient) -> None:
    await _complete_paid_visit(dashboard_client)
    admin = _headers(RoleName.ADMIN)
    overview = await dashboard_client.get("/api/v1/dashboard/overview", headers=admin)
    assert overview.status_code == 200, overview.text
    cards = overview.json()["data"]
    assert cards["revenue_today"] == "400.00"
    assert cards["revenue_this_month"] == "400.00"
    assert cards["appointments_today"] == 1
    assert cards["customers_served"] == 1
    assert cards["average_ticket_size"] == "400.00"

    revenue = await dashboard_client.get(
        "/api/v1/dashboard/revenue",
        params={"group_by": "day"},
        headers=admin,
    )
    assert revenue.status_code == 200
    assert revenue.json()["data"]["items"][0]["period"] == _today()
    assert revenue.json()["data"]["items"][0]["revenue"] == "400.00"

    appointments = await dashboard_client.get("/api/v1/dashboard/appointments", headers=admin)
    assert appointments.status_code == 200
    assert appointments.json()["data"]["items"][0]["completed"] == 1

    top = await dashboard_client.get("/api/v1/dashboard/top-performers", headers=admin)
    assert top.status_code == 200
    assert top.json()["data"]["items"][0]["staff_name"] == "Priya Sharma"
    assert top.json()["data"]["items"][0]["revenue"] == "400.00"


async def test_non_admin_cannot_read_dashboard(dashboard_client: AsyncClient) -> None:
    desk = await dashboard_client.get(
        "/api/v1/dashboard/overview",
        headers=_headers(RoleName.RECEPTIONIST),
    )
    assert desk.status_code == 403
    staff = await dashboard_client.get(
        "/api/v1/dashboard/overview",
        headers=_headers(RoleName.STAFF),
    )
    assert staff.status_code == 403
    anonymous = await dashboard_client.get("/api/v1/dashboard/overview")
    assert anonymous.status_code == 401
