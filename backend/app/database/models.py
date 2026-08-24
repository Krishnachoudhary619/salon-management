"""Import every mapped class so SQLAlchemy and Alembic share one metadata registry."""

from app.appointments.models import Appointment, AppointmentService
from app.auth.models import RefreshToken
from app.billing.models import Invoice, Payment
from app.commissions.models import Commission
from app.customers.models import Customer
from app.schedules.models import StaffSchedule
from app.services.models import Service
from app.staff.models import Staff
from app.tasks.models import Task
from app.tips.models import Tip
from app.users.models import Role, User, UserRole

__all__ = [
    "Appointment",
    "AppointmentService",
    "Commission",
    "Customer",
    "Invoice",
    "Payment",
    "RefreshToken",
    "Role",
    "Service",
    "Staff",
    "StaffSchedule",
    "Task",
    "Tip",
    "User",
    "UserRole",
]
