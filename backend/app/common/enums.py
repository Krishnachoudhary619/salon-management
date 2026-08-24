from enum import StrEnum


class Role(StrEnum):
    ADMIN = "ADMIN"
    RECEPTIONIST = "RECEPTIONIST"
    STAFF = "STAFF"


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


class StaffStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ON_LEAVE = "ON_LEAVE"


class AppointmentStatus(StrEnum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    ARRIVED = "ARRIVED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class PaymentMethod(StrEnum):
    CASH = "CASH"
    CARD = "CARD"
    UPI = "UPI"


class PaymentStatus(StrEnum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class TaskStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class Permission(StrEnum):
    USER_READ = "users:read"
    USER_WRITE = "users:write"

    STAFF_READ = "staff:read"
    STAFF_WRITE = "staff:write"
    STAFF_DELETE = "staff:delete"

    SERVICE_READ = "services:read"
    SERVICE_WRITE = "services:write"
    SERVICE_DELETE = "services:delete"

    CUSTOMER_READ = "customers:read"
    CUSTOMER_WRITE = "customers:write"

    SCHEDULE_READ = "schedules:read"
    SCHEDULE_WRITE = "schedules:write"

    APPOINTMENT_READ = "appointments:read"
    APPOINTMENT_READ_OWN = "appointments:read_own"
    APPOINTMENT_WRITE = "appointments:write"
    APPOINTMENT_WRITE_OWN = "appointments:write_own"

    PAYMENT_READ = "payments:read"
    PAYMENT_WRITE = "payments:write"
    INVOICE_READ = "invoices:read"

    COMMISSION_READ = "commissions:read"
    COMMISSION_READ_OWN = "commissions:read_own"
    COMMISSION_CONFIG = "commissions:config"

    TIP_READ = "tips:read"
    TIP_READ_OWN = "tips:read_own"
    TIP_WRITE = "tips:write"

    TASK_READ = "tasks:read"
    TASK_READ_OWN = "tasks:read_own"
    TASK_WRITE = "tasks:write"
    TASK_WRITE_OWN = "tasks:write_own"

    DASHBOARD_READ = "dashboard:read"
    REPORTS_READ = "reports:read"
    PERFORMANCE_READ = "performance:read"
    PERFORMANCE_READ_OWN = "performance:read_own"
