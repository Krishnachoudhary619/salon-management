from datetime import date, time
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload

from app.appointments.models import Appointment
from app.common.enums import AppointmentStatus
from app.common.repository import BaseRepository
from app.schedules.models import StaffSchedule
from app.services.models import Service
from app.staff.models import Staff

_BUSY_STATUSES = (
    AppointmentStatus.CANCELLED,
    AppointmentStatus.NO_SHOW,
)


class ScheduleRepository(BaseRepository[StaffSchedule]):
    """Database access for weekly working hours and busy appointment intervals."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, StaffSchedule)

    def _base_stmt(self, *, include_deleted: bool = False) -> Select[tuple[StaffSchedule]]:
        return (
            super()
            ._base_stmt(include_deleted=include_deleted)
            .options(noload(StaffSchedule.staff))
        )

    async def list_for_staff(
        self,
        staff_id: UUID,
        *,
        day_of_week: int | None = None,
        exclude_id: UUID | None = None,
    ) -> list[StaffSchedule]:
        stmt = self._base_stmt().where(StaffSchedule.staff_id == staff_id)
        if day_of_week is not None:
            stmt = stmt.where(StaffSchedule.day_of_week == day_of_week)
        if exclude_id is not None:
            stmt = stmt.where(StaffSchedule.id != exclude_id)
        stmt = stmt.order_by(StaffSchedule.day_of_week, StaffSchedule.start_time)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_staff(self, staff_id: UUID) -> Staff | None:
        stmt = (
            select(Staff)
            .where(Staff.id == staff_id, Staff.is_deleted.is_(False))
            .options(
                noload(Staff.user),
                noload(Staff.schedules),
                noload(Staff.appointments),
                noload(Staff.commissions),
                noload(Staff.tips),
                noload(Staff.tasks),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_service(self, service_id: UUID) -> Service | None:
        stmt = (
            select(Service)
            .where(Service.id == service_id, Service.is_deleted.is_(False))
            .options(noload(Service.appointment_services))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_busy_intervals(
        self,
        staff_id: UUID,
        on_date: date,
        *,
        exclude_appointment_id: UUID | None = None,
    ) -> list[tuple[time, time]]:
        stmt = select(Appointment.start_time, Appointment.end_time).where(
            Appointment.staff_id == staff_id,
            Appointment.appointment_date == on_date,
            Appointment.is_deleted.is_(False),
            Appointment.status.notin_(_BUSY_STATUSES),
        )
        if exclude_appointment_id is not None:
            stmt = stmt.where(Appointment.id != exclude_appointment_id)
        result = await self.session.execute(stmt)
        return [(row.start_time, row.end_time) for row in result.all()]
