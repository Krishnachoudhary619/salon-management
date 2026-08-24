from uuid import UUID

from app.common.enums import Role as RoleName
from app.common.enums import StaffStatus
from app.common.pagination import PaginatedData, PaginationParams
from app.common.service import BaseService
from app.core.exceptions import ConflictException, PermissionDeniedException, ValidationException
from app.core.logging import get_logger
from app.core.security import CurrentUser, hash_password
from app.staff.models import Staff
from app.staff.repository import StaffRepository
from app.staff.schemas import StaffCreateRequest, StaffResponse, StaffUpdateRequest
from app.users.models import User

logger = get_logger(__name__)

_ALLOWED_SORT = {"name", "created_at", "joining_date", "status", "commission_percentage", "phone"}


def to_staff_response(staff: Staff) -> StaffResponse:
    email = staff.user.email if staff.user is not None else None
    return StaffResponse(
        id=staff.id,
        user_id=staff.user_id,
        name=staff.name,
        email=email,
        phone=staff.phone,
        designation=staff.designation,
        commission_percentage=staff.commission_percentage,
        joining_date=staff.joining_date,
        status=staff.status,
        created_at=staff.created_at,
        updated_at=staff.updated_at,
    )


class StaffService(BaseService[Staff]):
    """Staff roster rules: unique phone/email, STAFF role, deactivate via soft delete."""

    def __init__(self, repository: StaffRepository) -> None:
        super().__init__(repository, resource_name="Staff")
        self.staff_repository = repository

    async def get_staff(self, staff_id: UUID) -> StaffResponse:
        staff = await self.get(staff_id)
        return to_staff_response(staff)

    async def list_staff(
        self,
        params: PaginationParams,
        *,
        status: StaffStatus | None = None,
    ) -> PaginatedData[StaffResponse]:
        filters = [Staff.status == status] if status is not None else None
        page = await self.staff_repository.list(
            params,
            filters=filters,
            search_fields=["name", "phone", "designation"],
            allowed_sort_fields=_ALLOWED_SORT,
        )
        return PaginatedData(
            items=[to_staff_response(item) for item in page.items],
            total=page.total,
            page=page.page,
            limit=page.limit,
        )

    async def create_staff(
        self,
        payload: StaffCreateRequest,
        *,
        actor: CurrentUser,
    ) -> StaffResponse:
        await self._ensure_unique_phone(payload.phone)
        if await self.staff_repository.get_user_by_email(str(payload.email)) is not None:
            raise ConflictException("A user with this email already exists")
        role = await self.staff_repository.get_role_by_name(RoleName.STAFF)
        if role is None:
            raise ValidationException("STAFF role is not configured")

        user = await self.staff_repository.create_user(
            User(
                name=payload.name,
                email=str(payload.email),
                password_hash=hash_password(payload.password),
                is_active=payload.status == StaffStatus.ACTIVE,
            )
        )
        await self.staff_repository.assign_role(user.id, role.id, actor_id=actor.id)
        staff = await self.staff_repository.create(
            Staff(
                user_id=user.id,
                name=payload.name,
                phone=payload.phone,
                designation=payload.designation,
                commission_percentage=payload.commission_percentage,
                joining_date=payload.joining_date,
                status=payload.status,
            ),
            created_by=actor.id,
        )
        loaded = await self.staff_repository.get_by_id(staff.id)
        assert loaded is not None
        logger.info("staff_created", staff_id=str(staff.id), user_id=str(user.id))
        return to_staff_response(loaded)

    async def update_staff(
        self,
        staff_id: UUID,
        payload: StaffUpdateRequest,
        *,
        actor: CurrentUser,
    ) -> StaffResponse:
        staff = await self.get(staff_id)
        changes = payload.model_dump(exclude_unset=True)
        if "phone" in changes:
            await self._ensure_unique_phone(changes["phone"], exclude_id=staff.id)
        if "commission_percentage" in changes and not actor.is_admin:
            raise PermissionDeniedException("Only ADMIN can change commission percentage")

        for field, value in changes.items():
            setattr(staff, field, value)
        if "name" in changes and staff.user is not None:
            staff.user.name = changes["name"]
        if "status" in changes and staff.user is not None:
            staff.user.is_active = changes["status"] == StaffStatus.ACTIVE

        await self.staff_repository.update(staff, updated_by=actor.id)
        loaded = await self.staff_repository.get_by_id(staff.id)
        assert loaded is not None
        logger.info("staff_updated", staff_id=str(staff.id))
        return to_staff_response(loaded)

    async def deactivate_staff(self, staff_id: UUID, *, actor: CurrentUser) -> None:
        staff = await self.get(staff_id)
        if staff.user_id == actor.id:
            raise PermissionDeniedException("You cannot deactivate your own staff profile")
        staff.status = StaffStatus.INACTIVE
        if staff.user is not None:
            staff.user.is_active = False
        await self.staff_repository.soft_delete(staff, deleted_by=actor.id)
        logger.info("staff_deactivated", staff_id=str(staff.id), user_id=str(staff.user_id))

    async def _ensure_unique_phone(self, phone: str, *, exclude_id: UUID | None = None) -> None:
        existing = await self.staff_repository.get_by_phone(phone, exclude_id=exclude_id)
        if existing is not None:
            raise ConflictException("A staff member with this phone already exists")
