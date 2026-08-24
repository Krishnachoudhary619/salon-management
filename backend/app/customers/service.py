from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app.common.pagination import PaginatedData, PaginationParams
from app.common.service import BaseService
from app.core.exceptions import ConflictException, ValidationException
from app.core.logging import get_logger
from app.core.security import CurrentUser
from app.customers.models import Customer
from app.customers.repository import CustomerRepository
from app.customers.schemas import CustomerCreateRequest, CustomerResponse, CustomerUpdateRequest

logger = get_logger(__name__)

_ALLOWED_SORT = {
    "name",
    "phone",
    "created_at",
    "updated_at",
    "visit_count",
    "total_spent",
    "last_visit",
}


def to_customer_response(customer: Customer) -> CustomerResponse:
    return CustomerResponse.model_validate(customer)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class CustomerService(BaseService[Customer]):
    """CRM rules: unique phone/email, search, profile, visit counters."""

    def __init__(self, repository: CustomerRepository) -> None:
        super().__init__(repository, resource_name="Customer")
        self.customer_repository = repository

    async def get_customer(self, customer_id: UUID) -> CustomerResponse:
        return to_customer_response(await self.get(customer_id))

    async def list_customers(
        self,
        params: PaginationParams,
        *,
        phone: str | None = None,
    ) -> PaginatedData[CustomerResponse]:
        filters = [Customer.phone == phone] if phone is not None else None
        page = await self.customer_repository.list(
            params,
            filters=filters,
            search_fields=["name", "phone", "email"],
            allowed_sort_fields=_ALLOWED_SORT,
        )
        return PaginatedData(
            items=[to_customer_response(item) for item in page.items],
            total=page.total,
            page=page.page,
            limit=page.limit,
        )

    async def create_customer(
        self,
        payload: CustomerCreateRequest,
        *,
        actor: CurrentUser,
    ) -> CustomerResponse:
        await self._ensure_unique_phone(payload.phone)
        await self._ensure_unique_email(str(payload.email) if payload.email else None)
        created = await self.customer_repository.create(
            Customer(
                name=payload.name,
                phone=payload.phone,
                email=str(payload.email) if payload.email else None,
                notes=payload.notes,
            ),
            created_by=actor.id,
        )
        logger.info("customer_created", customer_id=str(created.id))
        return to_customer_response(created)

    async def update_customer(
        self,
        customer_id: UUID,
        payload: CustomerUpdateRequest,
        *,
        actor: CurrentUser,
    ) -> CustomerResponse:
        customer = await self.get(customer_id)
        changes = payload.model_dump(exclude_unset=True)
        if "phone" in changes:
            await self._ensure_unique_phone(changes["phone"], exclude_id=customer.id)
        if "email" in changes:
            email = str(changes["email"]) if changes["email"] is not None else None
            await self._ensure_unique_email(email, exclude_id=customer.id)
            changes["email"] = email
        for field, value in changes.items():
            setattr(customer, field, value)
        updated = await self.customer_repository.update(customer, updated_by=actor.id)
        logger.info("customer_updated", customer_id=str(customer.id))
        return to_customer_response(updated)

    async def get_or_create_by_phone(
        self,
        payload: CustomerCreateRequest,
        *,
        actor: CurrentUser,
    ) -> CustomerResponse:
        existing = await self.customer_repository.get_by_phone(payload.phone)
        if existing is not None:
            return to_customer_response(existing)
        return await self.create_customer(payload, actor=actor)

    async def record_visit(
        self,
        customer_id: UUID,
        *,
        amount: Decimal,
        visited_at: datetime,
        actor: CurrentUser | None = None,
    ) -> CustomerResponse:
        if amount < 0:
            raise ValidationException("Visit amount cannot be negative")
        customer = await self.get(customer_id)
        customer.visit_count += 1
        customer.total_spent += amount
        if customer.last_visit is None or _as_utc(visited_at) >= _as_utc(customer.last_visit):
            customer.last_visit = visited_at
        actor_id = actor.id if actor is not None else None
        updated = await self.customer_repository.update(customer, updated_by=actor_id)
        logger.info(
            "customer_visit_recorded",
            customer_id=str(customer.id),
            visit_count=updated.visit_count,
        )
        return to_customer_response(updated)

    async def _ensure_unique_phone(self, phone: str, *, exclude_id: UUID | None = None) -> None:
        existing = await self.customer_repository.get_by_phone(phone, exclude_id=exclude_id)
        if existing is not None:
            raise ConflictException("A customer with this phone already exists")

    async def _ensure_unique_email(
        self,
        email: str | None,
        *,
        exclude_id: UUID | None = None,
    ) -> None:
        if email is None:
            return
        existing = await self.customer_repository.get_by_email(email, exclude_id=exclude_id)
        if existing is not None:
            raise ConflictException("A customer with this email already exists")
