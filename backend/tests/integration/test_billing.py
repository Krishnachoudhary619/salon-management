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
async def billing_client() -> AsyncGenerator[AsyncClient, None]:
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


async def _book(client: AsyncClient, *, start: str = "10:00:00") -> tuple[str, str, dict[str, str]]:
    staff_id, customer_id, service_id = await _seed(client)
    headers = _headers(RoleName.RECEPTIONIST)
    created = await client.post(
        "/api/v1/appointments",
        json={
            "customer_id": customer_id,
            "staff_id": staff_id,
            "appointment_date": "2026-08-24",
            "start_time": start,
            "service_ids": [service_id],
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    return created.json()["data"]["id"], customer_id, headers


async def _complete(client: AsyncClient, appointment_id: str, headers: dict[str, str]) -> None:
    for status in _WORKFLOW:
        response = await client.patch(
            f"/api/v1/appointments/{appointment_id}/status",
            json={"status": status},
            headers=headers,
        )
        assert response.status_code == 200, response.text


async def test_complete_pay_history_and_invoice_retrieval(billing_client: AsyncClient) -> None:
    appointment_id, customer_id, headers = await _book(billing_client)
    await _complete(billing_client, appointment_id, headers)

    invoices = await billing_client.get(
        "/api/v1/invoices",
        params={"appointment_id": appointment_id},
        headers=headers,
    )
    assert invoices.status_code == 200, invoices.text
    page = invoices.json()["data"]
    assert page["total"] == 1
    invoice = page["items"][0]
    invoice_id = invoice["id"]
    assert invoice["total"] == "400.00"
    assert invoice["is_paid"] is False
    assert invoice["line_items"][0]["service_name"] == "Hair Cut"

    cash = await billing_client.post(
        "/api/v1/payments",
        json={
            "appointment_id": appointment_id,
            "amount": "150.00",
            "payment_method": "CASH",
        },
        headers=headers,
    )
    assert cash.status_code == 201, cash.text
    assert cash.json()["data"]["payment_method"] == "CASH"
    assert cash.json()["data"]["payment_status"] == "SUCCESS"

    card = await billing_client.post(
        "/api/v1/payments",
        json={
            "appointment_id": appointment_id,
            "amount": "150.00",
            "payment_method": "CARD",
        },
        headers=headers,
    )
    upi = await billing_client.post(
        "/api/v1/payments",
        json={
            "appointment_id": appointment_id,
            "amount": "100.00",
            "payment_method": "UPI",
        },
        headers=headers,
    )
    assert card.status_code == 201, card.text
    assert upi.status_code == 201, upi.text

    detail = await billing_client.get(f"/api/v1/invoices/{invoice_id}", headers=headers)
    assert detail.status_code == 200
    body = detail.json()["data"]
    assert body["paid_amount"] == "400.00"
    assert body["is_paid"] is True

    history = await billing_client.get(
        "/api/v1/payments",
        params={"appointment_id": appointment_id, "payment_method": "UPI"},
        headers=headers,
    )
    assert history.status_code == 200
    assert history.json()["data"]["total"] == 1
    assert history.json()["data"]["items"][0]["payment_method"] == "UPI"

    customer = await billing_client.get(f"/api/v1/customers/{customer_id}", headers=headers)
    assert customer.status_code == 200
    assert customer.json()["data"]["visit_count"] == 1
    assert customer.json()["data"]["total_spent"] == "400.00"


async def test_pay_before_complete_and_cancelled_are_rejected(billing_client: AsyncClient) -> None:
    appointment_id, _customer_id, headers = await _book(billing_client)
    unpaid = await billing_client.post(
        "/api/v1/payments",
        json={
            "appointment_id": appointment_id,
            "amount": "400.00",
            "payment_method": "CASH",
        },
        headers=headers,
    )
    assert unpaid.status_code == 409

    cancelled = await billing_client.patch(
        f"/api/v1/appointments/{appointment_id}/cancel",
        headers=headers,
    )
    assert cancelled.status_code == 200
    blocked = await billing_client.post(
        "/api/v1/payments",
        json={
            "appointment_id": appointment_id,
            "amount": "400.00",
            "payment_method": "CASH",
        },
        headers=headers,
    )
    assert blocked.status_code == 409


async def test_staff_and_unauthenticated_are_denied(billing_client: AsyncClient) -> None:
    appointment_id, _customer_id, headers = await _book(billing_client)
    await _complete(billing_client, appointment_id, headers)
    staff = _headers(RoleName.STAFF)
    listed = await billing_client.get("/api/v1/payments", headers=staff)
    assert listed.status_code == 403
    invoices = await billing_client.get("/api/v1/invoices", headers=staff)
    assert invoices.status_code == 403
    created = await billing_client.post(
        "/api/v1/payments",
        json={
            "appointment_id": appointment_id,
            "amount": "400.00",
            "payment_method": "CASH",
        },
        headers=staff,
    )
    assert created.status_code == 403
    anonymous = await billing_client.get("/api/v1/payments")
    assert anonymous.status_code == 401


async def test_invalid_method_is_rejected(billing_client: AsyncClient) -> None:
    appointment_id, _customer_id, headers = await _book(billing_client)
    await _complete(billing_client, appointment_id, headers)
    response = await billing_client.post(
        "/api/v1/payments",
        json={
            "appointment_id": appointment_id,
            "amount": "400.00",
            "payment_method": "WALLET",
        },
        headers=headers,
    )
    assert response.status_code == 422
