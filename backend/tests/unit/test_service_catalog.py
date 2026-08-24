from collections.abc import AsyncGenerator
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.common.enums import Role as RoleName
from app.common.pagination import PaginationParams
from app.core.exceptions import ConflictException, NotFoundException
from app.core.security import CurrentUser
from app.database import models as _models  # noqa: F401
from app.database.base import Base
from app.services.repository import ServiceRepository
from app.services.schemas import ServiceCreateRequest, ServiceUpdateRequest
from app.services.service import ServiceService


@pytest.fixture
async def catalog_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as session:
        yield session
    await engine.dispose()


def _admin() -> CurrentUser:
    return CurrentUser(id=uuid4(), roles=[RoleName.ADMIN], email="admin@example.com")


def _create_payload(**overrides: object) -> ServiceCreateRequest:
    data: dict[str, object] = {
        "name": "Hair Cut",
        "description": "Classic haircut with wash and finish",
        "category": "Hair",
        "duration_minutes": 30,
        "price": Decimal("400.00"),
    }
    data.update(overrides)
    return ServiceCreateRequest.model_validate(data)


def _catalog(session: AsyncSession) -> ServiceService:
    return ServiceService(ServiceRepository(session))


async def test_create_service(catalog_session: AsyncSession) -> None:
    created = await _catalog(catalog_session).create_service(_create_payload(), actor=_admin())
    assert created.name == "Hair Cut"
    assert created.category == "Hair"
    assert created.duration_minutes == 30
    assert created.price == Decimal("400.00")
    assert created.is_active is True


async def test_create_service_rejects_duplicate_name(catalog_session: AsyncSession) -> None:
    catalog = _catalog(catalog_session)
    actor = _admin()
    await catalog.create_service(_create_payload(), actor=actor)
    with pytest.raises(ConflictException, match="name"):
        await catalog.create_service(
            _create_payload(name="hair cut", category="Beard"),
            actor=actor,
        )


async def test_update_and_list_services(catalog_session: AsyncSession) -> None:
    catalog = _catalog(catalog_session)
    actor = _admin()
    created = await catalog.create_service(_create_payload(), actor=actor)
    await catalog.create_service(
        _create_payload(
            name="Beard Trim",
            description="Beard shape and trim",
            category="Beard",
            duration_minutes=20,
            price=Decimal("250.00"),
        ),
        actor=actor,
    )
    updated = await catalog.update_service(
        created.id,
        ServiceUpdateRequest(price=Decimal("450.00"), duration_minutes=35),
        actor=actor,
    )
    assert updated.price == Decimal("450.00")
    assert updated.duration_minutes == 35

    page = await catalog.list_services(PaginationParams(page=1, limit=10, search="Hair"))
    assert page.total == 1
    assert page.items[0].id == created.id

    hair = await catalog.list_services(PaginationParams(page=1, limit=10), category="Hair")
    assert hair.total == 1


async def test_deactivate_hides_from_active_list(catalog_session: AsyncSession) -> None:
    catalog = _catalog(catalog_session)
    actor = _admin()
    created = await catalog.create_service(_create_payload(), actor=actor)
    await catalog.deactivate_service(created.id, actor=actor)

    active = await catalog.list_services(PaginationParams(page=1, limit=10), is_active=True)
    assert active.total == 0

    inactive = await catalog.list_services(PaginationParams(page=1, limit=10), is_active=False)
    assert inactive.total == 1
    assert inactive.items[0].is_active is False

    all_items = await catalog.list_services(PaginationParams(page=1, limit=10))
    assert all_items.total == 1


async def test_deactivate_missing_service(catalog_session: AsyncSession) -> None:
    with pytest.raises(NotFoundException):
        await _catalog(catalog_session).deactivate_service(uuid4(), actor=_admin())
