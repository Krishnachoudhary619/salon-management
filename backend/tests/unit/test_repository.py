from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import SortOrder
from app.common.pagination import PaginationParams
from app.common.repository import BaseRepository
from app.common.service import BaseService
from app.core.exceptions import NotFoundException, ValidationException
from tests.support.models import Widget


@pytest.fixture
def repository(db_session: AsyncSession) -> BaseRepository[Widget]:
    return BaseRepository(db_session, Widget)


@pytest.fixture
def service(repository: BaseRepository[Widget]) -> BaseService[Widget]:
    return BaseService(repository, resource_name="Widget")


async def test_create_get_and_audit_fields(
    repository: BaseRepository[Widget],
    db_session: AsyncSession,
) -> None:
    actor = uuid4()
    widget = await repository.create(Widget(name="Hair Cut"), created_by=actor)
    await db_session.commit()

    loaded = await repository.get_by_id(widget.id)
    assert loaded is not None
    assert loaded.name == "Hair Cut"
    assert loaded.created_by == actor
    assert loaded.updated_by == actor
    assert loaded.is_deleted is False
    assert loaded.created_at is not None
    assert loaded.updated_at is not None


async def test_soft_delete_hides_record(
    repository: BaseRepository[Widget],
    db_session: AsyncSession,
) -> None:
    widget = await repository.create(Widget(name="Beard Trim"))
    await repository.soft_delete(widget, deleted_by=uuid4())
    await db_session.commit()

    assert await repository.get_by_id(widget.id) is None
    restored = await repository.get_by_id(widget.id, include_deleted=True)
    assert restored is not None
    assert restored.is_deleted is True
    assert restored.deleted_at is not None


async def test_list_supports_search_sort_and_pagination(
    repository: BaseRepository[Widget],
    db_session: AsyncSession,
) -> None:
    await repository.create(Widget(name="Hair Cut"))
    await repository.create(Widget(name="Hair Color"))
    await repository.create(Widget(name="Facial"))
    await db_session.commit()

    page = await repository.list(
        PaginationParams(page=1, limit=1, search="Hair", sort_by="name", sort_order=SortOrder.ASC),
        search_fields=["name"],
        allowed_sort_fields={"name", "created_at"},
    )
    assert page.total == 2
    assert page.limit == 1
    assert page.items[0].name == "Hair Color"


async def test_invalid_sort_field_is_rejected(repository: BaseRepository[Widget]) -> None:
    with pytest.raises(ValidationException):
        await repository.list(
            PaginationParams(sort_by="password"),
            allowed_sort_fields={"name", "created_at"},
        )


async def test_base_service_get_and_not_found(
    service: BaseService[Widget],
    db_session: AsyncSession,
) -> None:
    created = await service.create(Widget(name="Spa"), actor_id=uuid4())
    await db_session.commit()

    loaded = await service.get(created.id)
    assert loaded.id == created.id

    with pytest.raises(NotFoundException, match="Widget not found"):
        await service.get(uuid4())


async def test_base_service_soft_deletes(
    service: BaseService[Widget],
    db_session: AsyncSession,
) -> None:
    created = await service.create(Widget(name="Color"), actor_id=uuid4())
    await service.delete(created.id, actor_id=uuid4())
    await db_session.commit()

    with pytest.raises(NotFoundException):
        await service.get(created.id)
