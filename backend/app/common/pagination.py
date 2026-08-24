from typing import Annotated

from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import SortOrder
from app.core.constants import DEFAULT_LIMIT, DEFAULT_PAGE, MAX_LIMIT


class PaginationParams:
    """Query parameters required on every list endpoint."""

    def __init__(
        self,
        page: Annotated[int, Query(ge=1, description="Page number")] = DEFAULT_PAGE,
        limit: Annotated[int, Query(ge=1, le=MAX_LIMIT, description="Page size")] = DEFAULT_LIMIT,
        search: Annotated[str | None, Query(description="Case-insensitive search")] = None,
        sort_by: Annotated[str | None, Query(description="Field to sort by")] = None,
        sort_order: Annotated[SortOrder, Query(description="Sort direction")] = SortOrder.DESC,
    ) -> None:
        self.page = page
        self.limit = limit
        self.search = search.strip() if search else None
        self.sort_by = sort_by
        self.sort_order = sort_order

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PaginatedData[T](BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    items: list[T]
    total: int
    page: int
    limit: int = Field(..., ge=1)
