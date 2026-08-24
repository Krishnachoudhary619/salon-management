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
async def tasks_client() -> AsyncGenerator[AsyncClient, None]:
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


async def _seed_staff(client: AsyncClient) -> tuple[str, str]:
    admin = _headers(RoleName.ADMIN)
    staff = await client.post("/api/v1/staff", json=STAFF_BODY, headers=admin)
    assert staff.status_code == 201, staff.text
    body = staff.json()["data"]
    return body["id"], body["user_id"]


async def test_admin_assigns_and_lists_tasks(tasks_client: AsyncClient) -> None:
    staff_id, user_id = await _seed_staff(tasks_client)
    admin = _headers(RoleName.ADMIN)
    created = await tasks_client.post(
        "/api/v1/tasks",
        json={
            "assigned_staff_id": staff_id,
            "title": "Restock shampoo",
            "description": "Front shelf",
            "due_date": "2026-08-25",
        },
        headers=admin,
    )
    assert created.status_code == 201, created.text
    body = created.json()["data"]
    task_id = body["id"]
    assert body["status"] == "PENDING"
    assert body["assigned_staff_name"] == "Priya Sharma"

    listed = await tasks_client.get("/api/v1/tasks", headers=admin)
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 1

    started = await tasks_client.put(
        f"/api/v1/tasks/{task_id}",
        json={"status": "IN_PROGRESS"},
        headers=_headers(RoleName.STAFF, subject=user_id),
    )
    assert started.status_code == 200, started.text
    assert started.json()["data"]["status"] == "IN_PROGRESS"

    done = await tasks_client.put(
        f"/api/v1/tasks/{task_id}",
        json={"status": "COMPLETED"},
        headers=admin,
    )
    assert done.status_code == 200
    assert done.json()["data"]["status"] == "COMPLETED"
    assert done.json()["data"]["completed_at"] is not None

    skipped = await tasks_client.post(
        "/api/v1/tasks",
        json={"assigned_staff_id": staff_id, "title": "Laundry"},
        headers=admin,
    )
    task_id = skipped.json()["data"]["id"]
    blocked = await tasks_client.put(
        f"/api/v1/tasks/{task_id}",
        json={"status": "COMPLETED"},
        headers=admin,
    )
    assert blocked.status_code == 422


async def test_staff_cannot_assign_and_receptionist_is_denied(
    tasks_client: AsyncClient,
) -> None:
    staff_id, user_id = await _seed_staff(tasks_client)
    created = await tasks_client.post(
        "/api/v1/tasks",
        json={"assigned_staff_id": staff_id, "title": "Clean stations"},
        headers=_headers(RoleName.STAFF, subject=user_id),
    )
    assert created.status_code == 403

    desk = await tasks_client.get("/api/v1/tasks", headers=_headers(RoleName.RECEPTIONIST))
    assert desk.status_code == 403

    anonymous = await tasks_client.get("/api/v1/tasks")
    assert anonymous.status_code == 401
