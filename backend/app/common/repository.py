from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from app.common.enums import SortOrder
from app.common.pagination import PaginatedData, PaginationParams
from app.core.exceptions import ValidationException
from app.database.base import BaseModel


class BaseRepository[ModelT: BaseModel]:
    """Generic async repository. Contains database operations only."""

    def __init__(self, session: AsyncSession, model: type[ModelT]) -> None:
        self.session = session
        self.model = model

    def _not_deleted(self) -> ColumnElement[bool]:
        return self.model.is_deleted.is_(False)

    def _base_stmt(self, *, include_deleted: bool = False) -> Select[tuple[ModelT]]:
        stmt = select(self.model)
        if not include_deleted:
            stmt = stmt.where(self._not_deleted())
        return stmt

    def _resolve_column(self, field_name: str) -> Any:
        column = getattr(self.model, field_name, None)
        if column is None:
            raise ValidationException(
                "Invalid sort or search field",
                errors=[{"field": field_name, "message": f"Unknown field '{field_name}'"}],
            )
        return column

    def _apply_search(
        self,
        stmt: Select[tuple[ModelT]],
        params: PaginationParams,
        search_fields: Sequence[str] | None,
    ) -> Select[tuple[ModelT]]:
        if not params.search or not search_fields:
            return stmt
        escaped = params.search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        clauses = [
            self._resolve_column(field).ilike(f"%{escaped}%", escape="\\")
            for field in search_fields
        ]
        return stmt.where(or_(*clauses))

    def _apply_sort(
        self,
        stmt: Select[tuple[ModelT]],
        params: PaginationParams,
        allowed_sort_fields: set[str] | None,
    ) -> Select[tuple[ModelT]]:
        sort_field = params.sort_by or "created_at"
        if allowed_sort_fields is not None and sort_field not in allowed_sort_fields:
            raise ValidationException(
                "Invalid sort field",
                errors=[
                    {"field": "sort_by", "message": f"Sorting by '{sort_field}' is not allowed"}
                ],
            )
        column = self._resolve_column(sort_field)
        order_clause = column.asc() if params.sort_order == SortOrder.ASC else column.desc()
        return stmt.order_by(order_clause)

    async def get_by_id(self, id: UUID, *, include_deleted: bool = False) -> ModelT | None:
        stmt = self._base_stmt(include_deleted=include_deleted).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists(self, id: UUID, *, include_deleted: bool = False) -> bool:
        return await self.get_by_id(id, include_deleted=include_deleted) is not None

    async def list(
        self,
        params: PaginationParams,
        *,
        filters: Sequence[ColumnElement[bool]] | None = None,
        search_fields: Sequence[str] | None = None,
        allowed_sort_fields: set[str] | None = None,
        include_deleted: bool = False,
    ) -> PaginatedData[ModelT]:
        stmt = self._base_stmt(include_deleted=include_deleted)
        for condition in filters or []:
            stmt = stmt.where(condition)
        stmt = self._apply_search(stmt, params, search_fields)

        count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
        total = int((await self.session.execute(count_stmt)).scalar_one())

        stmt = self._apply_sort(stmt, params, allowed_sort_fields)
        stmt = stmt.offset(params.offset).limit(params.limit)
        items = list((await self.session.execute(stmt)).scalars().all())
        return PaginatedData(items=items, total=total, page=params.page, limit=params.limit)

    async def create(self, instance: ModelT, *, created_by: UUID | None = None) -> ModelT:
        if created_by is not None:
            instance.created_by = created_by
            instance.updated_by = created_by
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, instance: ModelT, *, updated_by: UUID | None = None) -> ModelT:
        if updated_by is not None:
            instance.updated_by = updated_by
        instance.updated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def soft_delete(self, instance: ModelT, *, deleted_by: UUID | None = None) -> ModelT:
        instance.is_deleted = True
        instance.deleted_at = datetime.now(UTC)
        if deleted_by is not None:
            instance.updated_by = deleted_by
        await self.session.flush()
        return instance
