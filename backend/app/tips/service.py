from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from app.appointments.models import Appointment
from app.appointments.repository import AppointmentRepository
from app.common.enums import AppointmentStatus, Permission, SortOrder
from app.common.pagination import PaginatedData, PaginationParams
from app.common.service import BaseService
from app.core.exceptions import ConflictException, NotFoundException, PermissionDeniedException
from app.core.logging import get_logger
from app.core.permissions import has_permission
from app.core.security import CurrentUser
from app.staff.repository import StaffRepository
from app.tips.models import Tip
from app.tips.repository import TipRepository
from app.tips.schemas import TipCreateRequest, TipResponse, TipUpdateRequest

logger = get_logger(__name__)

_MONEY = Decimal("0.01")
_ALLOWED_SORT = {"created_at", "updated_at", "amount", "staff_id"}
_BLOCKED_STATUSES = frozenset({AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW})


def _money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(_MONEY, rounding=ROUND_HALF_UP)


def to_tip_response(tip: Tip) -> TipResponse:
    staff_name = tip.staff.name if tip.staff is not None else ""
    return TipResponse(
        id=tip.id,
        appointment_id=tip.appointment_id,
        staff_id=tip.staff_id,
        staff_name=staff_name,
        amount=_money(tip.amount),
        notes=tip.notes,
        created_at=tip.created_at,
        updated_at=tip.updated_at,
    )


class TipService(BaseService[Tip]):
    """Discretionary tips, stored separately from commission."""

    def __init__(
        self,
        repository: TipRepository,
        *,
        appointment_repository: AppointmentRepository,
        staff_repository: StaffRepository,
    ) -> None:
        super().__init__(repository, resource_name="Tip")
        self.tip_repository = repository
        self.appointment_repository = appointment_repository
        self.staff_repository = staff_repository

    async def create_tip(self, payload: TipCreateRequest, *, actor: CurrentUser) -> TipResponse:
        appointment = await self._require_open_appointment(payload.appointment_id)
        created = await self.tip_repository.create(
            Tip(
                appointment_id=appointment.id,
                staff_id=appointment.staff_id,
                amount=_money(payload.amount),
                notes=payload.notes,
            ),
            created_by=actor.id,
        )
        logger.info(
            "tip_created",
            tip_id=str(created.id),
            appointment_id=str(appointment.id),
            staff_id=str(appointment.staff_id),
        )
        loaded = await self.tip_repository.get_by_id(created.id)
        assert loaded is not None
        return to_tip_response(loaded)

    async def update_tip(
        self,
        tip_id: UUID,
        payload: TipUpdateRequest,
        *,
        actor: CurrentUser,
    ) -> TipResponse:
        tip = await self.get(tip_id)
        await self._require_open_appointment(tip.appointment_id)
        changes = payload.model_dump(exclude_unset=True)
        if "amount" in changes:
            tip.amount = _money(changes["amount"])
        if "notes" in changes:
            tip.notes = changes["notes"]
        await self.tip_repository.update(tip, updated_by=actor.id)
        loaded = await self.tip_repository.get_by_id(tip.id)
        assert loaded is not None
        logger.info("tip_updated", tip_id=str(tip.id))
        return to_tip_response(loaded)

    async def get_tip(self, tip_id: UUID, *, actor: CurrentUser) -> TipResponse:
        tip = await self.get(tip_id)
        await self._ensure_can_access(tip, actor)
        return to_tip_response(tip)

    async def list_tips(
        self,
        params: PaginationParams,
        *,
        actor: CurrentUser,
        staff_id: UUID | None = None,
        appointment_id: UUID | None = None,
    ) -> PaginatedData[TipResponse]:
        scoped_staff_id = await self._scoped_staff_id(actor, staff_id)
        if params.sort_by is None:
            params.sort_by = "created_at"
            params.sort_order = SortOrder.DESC
        filters = []
        if scoped_staff_id is not None:
            filters.append(Tip.staff_id == scoped_staff_id)
        if appointment_id is not None:
            filters.append(Tip.appointment_id == appointment_id)
        page = await self.tip_repository.list(
            params,
            filters=filters or None,
            search_fields=["notes"],
            allowed_sort_fields=_ALLOWED_SORT,
        )
        return PaginatedData(
            items=[to_tip_response(item) for item in page.items],
            total=page.total,
            page=page.page,
            limit=page.limit,
        )

    async def list_staff_tips(
        self,
        staff_id: UUID,
        params: PaginationParams,
        *,
        actor: CurrentUser,
    ) -> PaginatedData[TipResponse]:
        staff = await self.staff_repository.get_by_id(staff_id)
        if staff is None:
            raise NotFoundException("Staff not found")
        return await self.list_tips(params, actor=actor, staff_id=staff_id)

    async def _require_open_appointment(self, appointment_id: UUID) -> Appointment:
        appointment = await self.appointment_repository.get_by_id(appointment_id)
        if appointment is None:
            raise NotFoundException("Appointment not found")
        if appointment.status in _BLOCKED_STATUSES:
            raise ConflictException("Cannot record a tip on a cancelled or no-show appointment")
        return appointment

    async def _scoped_staff_id(
        self,
        actor: CurrentUser,
        requested_staff_id: UUID | None,
    ) -> UUID | None:
        if has_permission(actor, Permission.TIP_READ):
            return requested_staff_id
        profile = await self.staff_repository.get_by_user_id(actor.id)
        if profile is None:
            raise PermissionDeniedException("No staff profile is linked to this account")
        if requested_staff_id is not None and requested_staff_id != profile.id:
            raise PermissionDeniedException("You can only access your own tips")
        return profile.id

    async def _ensure_can_access(self, tip: Tip, actor: CurrentUser) -> None:
        scoped = await self._scoped_staff_id(actor, None)
        if scoped is not None and tip.staff_id != scoped:
            raise PermissionDeniedException("You can only access your own tips")
