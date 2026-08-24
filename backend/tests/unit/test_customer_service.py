from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.common.enums import Role as RoleName
from app.common.pagination import PaginationParams
from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.core.security import CurrentUser
from app.customers.repository import CustomerRepository
from app.customers.schemas import CustomerCreateRequest, CustomerUpdateRequest
from app.customers.service import CustomerService
from app.database import models as _models  # noqa: F401
from app.database.base import Base


@pytest.fixture
async def customer_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as session:
        yield session
    await engine.dispose()


def _admin() -> CurrentUser:
    return CurrentUser(id=uuid4(), roles=[RoleName.ADMIN], email="admin@example.com")


def _create_payload(**overrides: object) -> CustomerCreateRequest:
    data: dict[str, object] = {
        "name": "Meera Patel",
        "phone": "9876510001",
        "email": "meera@example.com",
        "notes": "Prefers morning slots",
    }
    data.update(overrides)
    return CustomerCreateRequest.model_validate(data)


def _crm(session: AsyncSession) -> CustomerService:
    return CustomerService(CustomerRepository(session))


async def test_create_customer_starts_with_zero_visits(customer_session: AsyncSession) -> None:
    created = await _crm(customer_session).create_customer(_create_payload(), actor=_admin())
    assert created.name == "Meera Patel"
    assert created.phone == "9876510001"
    assert created.email == "meera@example.com"
    assert created.visit_count == 0
    assert created.total_spent == Decimal("0.00")
    assert created.last_visit is None


async def test_create_customer_rejects_duplicate_phone(customer_session: AsyncSession) -> None:
    crm = _crm(customer_session)
    actor = _admin()
    await crm.create_customer(_create_payload(), actor=actor)
    with pytest.raises(ConflictException, match="phone"):
        await crm.create_customer(
            _create_payload(email="other@example.com", phone="9876510001"),
            actor=actor,
        )


async def test_create_customer_rejects_duplicate_email(customer_session: AsyncSession) -> None:
    crm = _crm(customer_session)
    actor = _admin()
    await crm.create_customer(_create_payload(), actor=actor)
    with pytest.raises(ConflictException, match="email"):
        await crm.create_customer(
            _create_payload(email="meera@example.com", phone="9876510002"),
            actor=actor,
        )


async def test_update_and_search_customers(customer_session: AsyncSession) -> None:
    crm = _crm(customer_session)
    actor = _admin()
    created = await crm.create_customer(_create_payload(), actor=actor)
    await crm.create_customer(
        _create_payload(name="Arjun Shah", phone="9876510002", email="arjun@example.com"),
        actor=actor,
    )
    updated = await crm.update_customer(
        created.id,
        CustomerUpdateRequest(notes="Color-treated hair"),
        actor=actor,
    )
    assert updated.notes == "Color-treated hair"

    page = await crm.list_customers(PaginationParams(page=1, limit=10, search="Meera"))
    assert page.total == 1
    assert page.items[0].id == created.id

    by_phone = await crm.list_customers(PaginationParams(page=1, limit=10), phone="9876510001")
    assert by_phone.total == 1


async def test_get_or_create_by_phone_returns_existing(customer_session: AsyncSession) -> None:
    crm = _crm(customer_session)
    actor = _admin()
    first = await crm.get_or_create_by_phone(_create_payload(), actor=actor)
    second = await crm.get_or_create_by_phone(
        _create_payload(name="Different Name"),
        actor=actor,
    )
    assert first.id == second.id
    assert second.name == "Meera Patel"


async def test_record_visit_updates_profile_counters(customer_session: AsyncSession) -> None:
    crm = _crm(customer_session)
    actor = _admin()
    created = await crm.create_customer(_create_payload(), actor=actor)
    first_visit = datetime(2026, 8, 1, 10, 0, tzinfo=UTC)
    second_visit = first_visit + timedelta(days=7)

    after_first = await crm.record_visit(
        created.id,
        amount=Decimal("400.00"),
        visited_at=first_visit,
        actor=actor,
    )
    assert after_first.visit_count == 1
    assert after_first.total_spent == Decimal("400.00")
    assert after_first.last_visit is not None
    assert after_first.last_visit.replace(tzinfo=UTC) == first_visit

    after_second = await crm.record_visit(
        created.id,
        amount=Decimal("600.00"),
        visited_at=second_visit,
        actor=actor,
    )
    assert after_second.visit_count == 2
    assert after_second.total_spent == Decimal("1000.00")
    assert after_second.last_visit is not None
    assert after_second.last_visit.replace(tzinfo=UTC) == second_visit

    profile = await crm.get_customer(created.id)
    assert profile.visit_count == 2
    assert profile.total_spent == Decimal("1000.00")


async def test_record_visit_rejects_negative_amount(customer_session: AsyncSession) -> None:
    crm = _crm(customer_session)
    actor = _admin()
    created = await crm.create_customer(_create_payload(), actor=actor)
    with pytest.raises(ValidationException, match="negative"):
        await crm.record_visit(
            created.id,
            amount=Decimal("-1.00"),
            visited_at=datetime.now(UTC),
            actor=actor,
        )


async def test_profile_missing_customer(customer_session: AsyncSession) -> None:
    with pytest.raises(NotFoundException):
        await _crm(customer_session).get_customer(uuid4())
