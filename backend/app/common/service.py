from uuid import UUID

from sqlalchemy.sql import ColumnElement

from app.common.pagination import PaginatedData, PaginationParams
from app.common.repository import BaseRepository
from app.core.exceptions import NotFoundException
from app.database.base import BaseModel


class BaseService[ModelT: BaseModel]:
    """Generic service helpers. Domain rules belong in module services."""

    def __init__(
        self,
        repository: BaseRepository[ModelT],
        *,
        resource_name: str = "Resource",
    ) -> None:
        self.repository = repository
        self.resource_name = resource_name

    async def get(self, id: UUID) -> ModelT:
        instance = await self.repository.get_by_id(id)
        if instance is None:
            raise NotFoundException(f"{self.resource_name} not found")
        return instance

    async def list(
        self,
        params: PaginationParams,
        *,
        filters: list[ColumnElement[bool]] | None = None,
        search_fields: list[str] | None = None,
        allowed_sort_fields: set[str] | None = None,
    ) -> PaginatedData[ModelT]:
        return await self.repository.list(
            params,
            filters=filters,
            search_fields=search_fields,
            allowed_sort_fields=allowed_sort_fields,
        )

    async def create(self, instance: ModelT, *, actor_id: UUID | None = None) -> ModelT:
        return await self.repository.create(instance, created_by=actor_id)

    async def update(self, instance: ModelT, *, actor_id: UUID | None = None) -> ModelT:
        return await self.repository.update(instance, updated_by=actor_id)

    async def delete(self, id: UUID, *, actor_id: UUID | None = None) -> None:
        instance = await self.get(id)
        await self.repository.soft_delete(instance, deleted_by=actor_id)
