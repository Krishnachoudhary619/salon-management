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
_WORKFLOW = ("CONFIRMED", "ARRIVED", "IN_PROGRESS", "COMPLETED")


@pytest.fixture
async def commissions_client() -> AsyncGenerator[AsyncClient, None]:
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


async def _seed(client: AsyncClient) -> tuple[str, str, str, str]:
    admin = _headers(RoleName.ADMIN)
    staff = await client.post("/api/v1/staff", json=STAFF_BODY, headers=admin)
    assert staff.status_code == 201, staff.text
    body = staff.json()["data"]
    window = await client.post(
        "/api/v1/staff-schedules",
        json={
            "staff_id": body["id"],
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
    return body["id"], body["user_id"], customer.json()["data"]["id"], service.json()["data"]["id"]


async def _complete_and_pay(
    client: AsyncClient,
    *,
    staff_id: str,
    customer_id: str,
    service_id: str,
    start: str = "10:00:00",
) -> str:
    admin = _headers(RoleName.ADMIN)
    created = await client.post(
        "/api/v1/appointments",
        json={
            "customer_id": customer_id,
            "staff_id": staff_id,
            "appointment_date": "2026-08-24",
            "start_time": start,
            "service_ids": [service_id],
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
    return appointment_id


async def test_admin_lists_staff_commissions_after_payment(
    commissions_client: AsyncClient,
) -> None:
    staff_id, user_id, customer_id, service_id = await _seed(commissions_client)
    appointment_id = await _complete_and_pay(
        commissions_client,
        staff_id=staff_id,
        customer_id=customer_id,
        service_id=service_id,
    )
    admin = _headers(RoleName.ADMIN)
    listed = await commissions_client.get("/api/v1/commissions", headers=admin)
    assert listed.status_code == 200, listed.text
    page = listed.json()["data"]
    assert page["total"] == 1
    item = page["items"][0]
    assert item["appointment_id"] == appointment_id
    assert item["staff_id"] == staff_id
    assert item["service_revenue"] == "400.00"
    assert item["commission_percentage"] == "40.00"
    assert item["commission_amount"] == "160.00"

    by_staff = await commissions_client.get(
        f"/api/v1/commissions/staff/{staff_id}",
        headers=admin,
    )
    assert by_staff.status_code == 200
    assert by_staff.json()["data"]["total"] == 1

    detail = await commissions_client.get(
        f"/api/v1/commissions/{item['id']}",
        headers=admin,
    )
    assert detail.status_code == 200
    assert detail.json()["data"]["commission_amount"] == "160.00"

    own = await commissions_client.get(
        "/api/v1/commissions",
        headers=_headers(RoleName.STAFF, subject=user_id),
    )
    assert own.status_code == 200
    assert own.json()["data"]["total"] == 1


async def test_receptionist_and_unauthenticated_are_denied(
    commissions_client: AsyncClient,
) -> None:
    desk = await commissions_client.get(
        "/api/v1/commissions",
        headers=_headers(RoleName.RECEPTIONIST),
    )
    assert desk.status_code == 403
    anonymous = await commissions_client.get("/api/v1/commissions")
    assert anonymous.status_code == 401


async def test_staff_without_profile_is_denied(commissions_client: AsyncClient) -> None:
    response = await commissions_client.get(
        "/api/v1/commissions",
        headers=_headers(RoleName.STAFF),
    )
    assert response.status_code == 403
