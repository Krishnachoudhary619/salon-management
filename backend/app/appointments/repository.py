from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload, selectinload

from app.appointments.models import Appointment
from app.appointments.models import AppointmentService as AppointmentLine
from app.common.repository import BaseRepository
from app.customers.models import Customer
from app.services.models import Service
from app.staff.models import Staff


class AppointmentRepository(BaseRepository[Appointment]):
    """Database access for appointments and their service lines."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Appointment)

    def _base_stmt(self, *, include_deleted: bool = False) -> Select[tuple[Appointment]]:
        return (
            super()
            ._base_stmt(include_deleted=include_deleted)
            .options(
                selectinload(Appointment.appointment_services).options(
                    noload(AppointmentLine.appointment),
                    noload(AppointmentLine.service),
                ),
                selectinload(Appointment.customer).options(noload(Customer.appointments)),
                selectinload(Appointment.staff).options(
                    noload(Staff.user),
                    noload(Staff.schedules),
                    noload(Staff.appointments),
                    noload(Staff.commissions),
                    noload(Staff.tips),
                    noload(Staff.tasks),
                ),
                noload(Appointment.invoice),
                noload(Appointment.payments),
                noload(Appointment.commission),
                noload(Appointment.tips),
            )
            .execution_options(populate_existing=True)
        )

    async def list_in_range(
        self,
        start_date: date,
        end_date: date,
        *,
        staff_id: UUID | None = None,
        customer_id: UUID | None = None,
    ) -> list[Appointment]:
        stmt = self._base_stmt().where(
            Appointment.appointment_date >= start_date,
            Appointment.appointment_date <= end_date,
        )
        if staff_id is not None:
            stmt = stmt.where(Appointment.staff_id == staff_id)
        if customer_id is not None:
            stmt = stmt.where(Appointment.customer_id == customer_id)
        stmt = stmt.order_by(Appointment.appointment_date, Appointment.start_time)
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_catalog_services(self, service_ids: list[UUID]) -> list[Service]:
        if not service_ids:
            return []
        stmt = (
            select(Service)
            .where(Service.id.in_(service_ids), Service.is_deleted.is_(False))
            .options(noload(Service.appointment_services))
        )
        result = await self.session.execute(stmt)
        found = {item.id: item for item in result.scalars().all()}
        return [found[service_id] for service_id in service_ids if service_id in found]

    async def list_lines(
        self,
        appointment_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> list[AppointmentLine]:
        stmt = select(AppointmentLine).where(AppointmentLine.appointment_id == appointment_id)
        if not include_deleted:
            stmt = stmt.where(AppointmentLine.is_deleted.is_(False))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_line(self, line: AppointmentLine, *, created_by: UUID | None) -> AppointmentLine:
        if created_by is not None:
            line.created_by = created_by
            line.updated_by = created_by
        self.session.add(line)
        await self.session.flush()
        return line

    async def soft_delete_line(
        self,
        line: AppointmentLine,
        *,
        deleted_by: UUID | None,
    ) -> None:
        line.is_deleted = True
        line.deleted_at = datetime.now(UTC)
        if deleted_by is not None:
            line.updated_by = deleted_by
        await self.session.flush()
