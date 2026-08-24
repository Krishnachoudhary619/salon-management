from uuid import UUID

from app.common.pagination import PaginatedData, PaginationParams
from app.common.service import BaseService
from app.core.exceptions import ConflictException
from app.core.logging import get_logger
from app.core.security import CurrentUser
from app.services.models import Service
from app.services.repository import ServiceRepository
from app.services.schemas import ServiceCreateRequest, ServiceResponse, ServiceUpdateRequest

logger = get_logger(__name__)

_ALLOWED_SORT = {
    "name",
    "created_at",
    "updated_at",
    "price",
    "duration_minutes",
    "category",
    "is_active",
}


def to_service_response(service: Service) -> ServiceResponse:
    return ServiceResponse.model_validate(service)


class ServiceService(BaseService[Service]):
    """Catalog rules: unique name, price/duration checks, deactivate via is_active."""

    def __init__(self, repository: ServiceRepository) -> None:
        super().__init__(repository, resource_name="Service")
        self.service_repository = repository

    async def list_services(
        self,
        params: PaginationParams,
        *,
        is_active: bool | None = None,
        category: str | None = None,
    ) -> PaginatedData[ServiceResponse]:
        filters = []
        if is_active is not None:
            filters.append(Service.is_active.is_(is_active))
        if category is not None:
            filters.append(Service.category.ilike(category.strip()))
        page = await self.service_repository.list(
            params,
            filters=filters or None,
            search_fields=["name", "description", "category"],
            allowed_sort_fields=_ALLOWED_SORT,
        )
        return PaginatedData(
            items=[to_service_response(item) for item in page.items],
            total=page.total,
            page=page.page,
            limit=page.limit,
        )

    async def create_service(
        self,
        payload: ServiceCreateRequest,
        *,
        actor: CurrentUser,
    ) -> ServiceResponse:
        await self._ensure_unique_name(payload.name)
        created = await self.service_repository.create(
            Service(
                name=payload.name,
                description=payload.description,
                category=payload.category,
                duration_minutes=payload.duration_minutes,
                price=payload.price,
                is_active=payload.is_active,
            ),
            created_by=actor.id,
        )
        logger.info("service_created", service_id=str(created.id))
        return to_service_response(created)

    async def update_service(
        self,
        service_id: UUID,
        payload: ServiceUpdateRequest,
        *,
        actor: CurrentUser,
    ) -> ServiceResponse:
        service = await self.get(service_id)
        changes = payload.model_dump(exclude_unset=True)
        if "name" in changes:
            await self._ensure_unique_name(changes["name"], exclude_id=service.id)
        for field, value in changes.items():
            setattr(service, field, value)
        updated = await self.service_repository.update(service, updated_by=actor.id)
        logger.info("service_updated", service_id=str(service.id))
        return to_service_response(updated)

    async def deactivate_service(self, service_id: UUID, *, actor: CurrentUser) -> None:
        service = await self.get(service_id)
        service.is_active = False
        await self.service_repository.update(service, updated_by=actor.id)
        logger.info("service_deactivated", service_id=str(service.id))

    async def _ensure_unique_name(self, name: str, *, exclude_id: UUID | None = None) -> None:
        existing = await self.service_repository.get_by_name(name, exclude_id=exclude_id)
        if existing is not None:
            raise ConflictException("A service with this name already exists")
