from sqlalchemy.orm import configure_mappers

from app.database.base import Base
from app.database.models import (
    Appointment,
    AppointmentService,
    Commission,
    Customer,
    Invoice,
    Payment,
    RefreshToken,
    Role,
    Service,
    Staff,
    StaffSchedule,
    Task,
    Tip,
    User,
    UserRole,
)

EXPECTED_TABLES = {
    "roles",
    "users",
    "user_roles",
    "refresh_tokens",
    "staff",
    "services",
    "customers",
    "staff_schedules",
    "appointments",
    "appointment_services",
    "invoices",
    "payments",
    "commissions",
    "tips",
    "tasks",
}


def test_all_v1_tables_are_mapped() -> None:
    configure_mappers()
    assert set(Base.metadata.tables) >= EXPECTED_TABLES


def test_core_relationships_are_configured() -> None:
    configure_mappers()
    assert User.staff.property.uselist is False
    assert Appointment.invoice.property.uselist is False
    assert Appointment.commission.property.uselist is False
    assert Staff.user.property.mapper.class_ is User
    assert AppointmentService.appointment.property.mapper.class_ is Appointment
    assert Payment.appointment.property.mapper.class_ is Appointment
    assert RefreshToken.user.property.mapper.class_ is User
    assert Invoice.__tablename__ == "invoices"
    assert Role.__tablename__ == "roles"
    assert Customer.__tablename__ == "customers"
    assert Service.__tablename__ == "services"
    assert StaffSchedule.__tablename__ == "staff_schedules"
    assert Tip.__tablename__ == "tips"
    assert Task.__tablename__ == "tasks"
    assert UserRole.__tablename__ == "user_roles"
    assert Commission.__tablename__ == "commissions"
