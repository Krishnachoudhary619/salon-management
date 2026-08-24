"""Create V1 salon tables from approved models.

Revision ID: 0002_create_v1_schema
Revises: 0001_foundation
Create Date: 2026-08-24

Domain enums are VARCHAR columns with CHECK constraints, not PostgreSQL ENUM types.
Partial unique indexes apply only to active (is_deleted = false) rows.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_create_v1_schema"
down_revision: str | Sequence[str] | None = "0001_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ACTIVE_ROW = sa.text("is_deleted = false")
UNSCOPED_BRANCH = sa.text(
    "coalesce(branch_id, CAST('00000000-0000-0000-0000-000000000000' AS UUID))"
)


def _base_columns(*, branch: bool = False) -> list[sa.Column]:
    columns = [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]
    if branch:
        columns.append(sa.Column("branch_id", sa.Uuid(), nullable=True))
    return columns


def _mixin_indexes(table: str, *, branch: bool = False) -> None:
    op.create_index(f"ix_{table}_is_deleted", table, ["is_deleted"])
    if branch:
        op.create_index(f"ix_{table}_branch_id", table, ["branch_id"])


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("name", sa.String(32), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name="pk_roles"),
        sa.CheckConstraint(
            "name IN ('ADMIN', 'RECEPTIONIST', 'STAFF')",
            name="name_allowed",
        ),
    )
    _mixin_indexes("roles")
    op.create_index(
        "uq_roles_name_active",
        "roles",
        ["name"],
        unique=True,
        postgresql_where=ACTIVE_ROW,
    )

    op.create_table(
        "users",
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
    )
    _mixin_indexes("users")
    op.create_index("ix_users_is_active", "users", ["is_active"])
    op.create_index(
        "uq_users_email_active",
        "users",
        [sa.text("lower(email)")],
        unique=True,
        postgresql_where=ACTIVE_ROW,
    )

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name="pk_user_roles"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_user_roles_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            name="fk_user_roles_role_id_roles",
            ondelete="RESTRICT",
        ),
    )
    _mixin_indexes("user_roles")
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"])
    op.create_index(
        "uq_user_roles_user_role_active",
        "user_roles",
        ["user_id", "role_id"],
        unique=True,
        postgresql_where=ACTIVE_ROW,
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("jti", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by_id", sa.Uuid(), nullable=True),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name="pk_refresh_tokens"),
        sa.UniqueConstraint("jti", name="uq_refresh_tokens_jti"),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_refresh_tokens_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["replaced_by_id"],
            ["refresh_tokens.id"],
            name="fk_refresh_tokens_replaced_by_id_refresh_tokens",
            ondelete="SET NULL",
        ),
    )
    _mixin_indexes("refresh_tokens")
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])
    op.create_index(
        "ix_refresh_tokens_user_revoked_expires",
        "refresh_tokens",
        ["user_id", "revoked_at", "expires_at"],
    )

    op.create_table(
        "staff",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("phone", sa.String(15), nullable=False),
        sa.Column("designation", sa.String(80), nullable=False),
        sa.Column("commission_percentage", sa.Numeric(5, 2), nullable=False),
        sa.Column("joining_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            server_default="ACTIVE",
            nullable=False,
        ),
        *_base_columns(branch=True),
        sa.PrimaryKeyConstraint("id", name="pk_staff"),
        sa.CheckConstraint(
            "commission_percentage >= 0 AND commission_percentage <= 100",
            name="commission_percentage",
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE', 'ON_LEAVE')",
            name="status_allowed",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_staff_user_id_users",
            ondelete="RESTRICT",
        ),
    )
    _mixin_indexes("staff", branch=True)
    op.create_index("ix_staff_status", "staff", ["status"])
    op.create_index("ix_staff_name", "staff", ["name"])
    op.create_index(
        "uq_staff_user_id_active",
        "staff",
        ["user_id"],
        unique=True,
        postgresql_where=ACTIVE_ROW,
    )
    op.create_index(
        "uq_staff_phone_active",
        "staff",
        ["phone"],
        unique=True,
        postgresql_where=ACTIVE_ROW,
    )

    op.create_table(
        "services",
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        *_base_columns(branch=True),
        sa.PrimaryKeyConstraint("id", name="pk_services"),
        sa.CheckConstraint(
            "duration_minutes > 0",
            name="duration_minutes_positive",
        ),
        sa.CheckConstraint("price > 0", name="price_positive"),
    )
    _mixin_indexes("services", branch=True)
    op.create_index(
        "ix_services_category_is_active",
        "services",
        ["category", "is_active"],
    )
    op.create_index(
        "uq_services_name_branch_active",
        "services",
        [sa.text("lower(name)"), UNSCOPED_BRANCH],
        unique=True,
        postgresql_where=ACTIVE_ROW,
    )

    op.create_table(
        "customers",
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("phone", sa.String(15), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column(
            "visit_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "total_spent",
            sa.Numeric(12, 2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("last_visit", sa.DateTime(timezone=True), nullable=True),
        *_base_columns(branch=True),
        sa.PrimaryKeyConstraint("id", name="pk_customers"),
        sa.CheckConstraint(
            "visit_count >= 0",
            name="visit_count_non_negative",
        ),
        sa.CheckConstraint(
            "total_spent >= 0",
            name="total_spent_non_negative",
        ),
    )
    _mixin_indexes("customers", branch=True)
    op.create_index("ix_customers_name", "customers", ["name"])
    op.create_index("ix_customers_last_visit", "customers", ["last_visit"])
    op.create_index(
        "uq_customers_phone_active",
        "customers",
        ["phone"],
        unique=True,
        postgresql_where=ACTIVE_ROW,
    )
    op.create_index(
        "uq_customers_email_active",
        "customers",
        [sa.text("lower(email)")],
        unique=True,
        postgresql_where=sa.text("email IS NOT NULL AND is_deleted = false"),
    )

    op.create_table(
        "staff_schedules",
        sa.Column("staff_id", sa.Uuid(), nullable=False),
        sa.Column("day_of_week", sa.SmallInteger(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        *_base_columns(branch=True),
        sa.PrimaryKeyConstraint("id", name="pk_staff_schedules"),
        sa.CheckConstraint(
            "day_of_week BETWEEN 0 AND 6",
            name="day_of_week_range",
        ),
        sa.CheckConstraint(
            "end_time > start_time",
            name="end_after_start",
        ),
        sa.ForeignKeyConstraint(
            ["staff_id"],
            ["staff.id"],
            name="fk_staff_schedules_staff_id_staff",
            ondelete="RESTRICT",
        ),
    )
    _mixin_indexes("staff_schedules", branch=True)
    op.create_index(
        "ix_staff_schedules_staff_day_active",
        "staff_schedules",
        ["staff_id", "day_of_week"],
        postgresql_where=ACTIVE_ROW,
    )

    op.create_table(
        "appointments",
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("staff_id", sa.Uuid(), nullable=False),
        sa.Column("appointment_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *_base_columns(branch=True),
        sa.PrimaryKeyConstraint("id", name="pk_appointments"),
        sa.CheckConstraint(
            "end_time > start_time",
            name="end_after_start",
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'CONFIRMED', 'ARRIVED', 'IN_PROGRESS',"
            " 'COMPLETED', 'CANCELLED', 'NO_SHOW')",
            name="status_allowed",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            name="fk_appointments_customer_id_customers",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["staff_id"],
            ["staff.id"],
            name="fk_appointments_staff_id_staff",
            ondelete="RESTRICT",
        ),
    )
    _mixin_indexes("appointments", branch=True)
    op.create_index(
        "ix_appointments_staff_slot_active",
        "appointments",
        ["staff_id", "appointment_date", "start_time", "end_time"],
        postgresql_where=ACTIVE_ROW,
    )
    op.create_index(
        "ix_appointments_date_status",
        "appointments",
        ["appointment_date", "status"],
    )
    op.create_index("ix_appointments_customer_id", "appointments", ["customer_id"])
    op.create_index("ix_appointments_status", "appointments", ["status"])
    op.create_index("ix_appointments_completed_at", "appointments", ["completed_at"])

    op.create_table(
        "appointment_services",
        sa.Column("appointment_id", sa.Uuid(), nullable=False),
        sa.Column("service_id", sa.Uuid(), nullable=False),
        sa.Column("service_name_snapshot", sa.String(120), nullable=False),
        sa.Column("duration_minutes_snapshot", sa.Integer(), nullable=False),
        sa.Column("price_snapshot", sa.Numeric(12, 2), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name="pk_appointment_services"),
        sa.CheckConstraint(
            "duration_minutes_snapshot > 0",
            name="duration_minutes_snapshot_positive",
        ),
        sa.CheckConstraint(
            "price_snapshot > 0",
            name="price_snapshot_positive",
        ),
        sa.ForeignKeyConstraint(
            ["appointment_id"],
            ["appointments.id"],
            name="fk_appointment_services_appointment_id_appointments",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["service_id"],
            ["services.id"],
            name="fk_appointment_services_service_id_services",
            ondelete="RESTRICT",
        ),
    )
    _mixin_indexes("appointment_services")
    op.create_index(
        "ix_appointment_services_appointment_id",
        "appointment_services",
        ["appointment_id"],
    )
    op.create_index(
        "ix_appointment_services_service_id",
        "appointment_services",
        ["service_id"],
    )
    op.create_index(
        "uq_appointment_services_appointment_service_active",
        "appointment_services",
        ["appointment_id", "service_id"],
        unique=True,
        postgresql_where=ACTIVE_ROW,
    )

    op.create_table(
        "invoices",
        sa.Column("appointment_id", sa.Uuid(), nullable=False),
        sa.Column("invoice_number", sa.String(40), nullable=False),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "tax",
            sa.Numeric(12, 2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        *_base_columns(branch=True),
        sa.PrimaryKeyConstraint("id", name="pk_invoices"),
        sa.CheckConstraint(
            "subtotal >= 0",
            name="subtotal_non_negative",
        ),
        sa.CheckConstraint("tax >= 0", name="tax_non_negative"),
        sa.CheckConstraint(
            "total = subtotal + tax",
            name="total_matches_subtotal_tax",
        ),
        sa.CheckConstraint("total > 0", name="total_positive"),
        sa.ForeignKeyConstraint(
            ["appointment_id"],
            ["appointments.id"],
            name="fk_invoices_appointment_id_appointments",
            ondelete="RESTRICT",
        ),
    )
    _mixin_indexes("invoices", branch=True)
    op.create_index("ix_invoices_created_at", "invoices", ["created_at"])
    op.create_index(
        "uq_invoices_appointment_id_active",
        "invoices",
        ["appointment_id"],
        unique=True,
        postgresql_where=ACTIVE_ROW,
    )
    op.create_index(
        "uq_invoices_invoice_number_active",
        "invoices",
        ["invoice_number"],
        unique=True,
        postgresql_where=ACTIVE_ROW,
    )

    op.create_table(
        "payments",
        sa.Column("appointment_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("payment_method", sa.String(20), nullable=False),
        sa.Column(
            "payment_status",
            sa.String(20),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        *_base_columns(branch=True),
        sa.PrimaryKeyConstraint("id", name="pk_payments"),
        sa.CheckConstraint("amount > 0", name="amount_positive"),
        sa.CheckConstraint(
            "payment_method IN ('CASH', 'CARD', 'UPI')",
            name="payment_method_allowed",
        ),
        sa.CheckConstraint(
            "payment_status IN ('PENDING', 'SUCCESS', 'FAILED', 'REFUNDED')",
            name="payment_status_allowed",
        ),
        sa.CheckConstraint(
            "(payment_status <> 'SUCCESS') OR (paid_at IS NOT NULL)",
            name="success_requires_paid_at",
        ),
        sa.ForeignKeyConstraint(
            ["appointment_id"],
            ["appointments.id"],
            name="fk_payments_appointment_id_appointments",
            ondelete="RESTRICT",
        ),
    )
    _mixin_indexes("payments", branch=True)
    op.create_index("ix_payments_appointment_id", "payments", ["appointment_id"])
    op.create_index(
        "ix_payments_paid_at_status",
        "payments",
        ["paid_at", "payment_status"],
    )
    op.create_index(
        "ix_payments_status_created_at",
        "payments",
        ["payment_status", "created_at"],
    )

    op.create_table(
        "commissions",
        sa.Column("appointment_id", sa.Uuid(), nullable=False),
        sa.Column("staff_id", sa.Uuid(), nullable=False),
        sa.Column("service_revenue", sa.Numeric(12, 2), nullable=False),
        sa.Column("commission_percentage", sa.Numeric(5, 2), nullable=False),
        sa.Column("commission_amount", sa.Numeric(12, 2), nullable=False),
        *_base_columns(branch=True),
        sa.PrimaryKeyConstraint("id", name="pk_commissions"),
        sa.CheckConstraint(
            "service_revenue > 0",
            name="service_revenue_positive",
        ),
        sa.CheckConstraint(
            "commission_percentage >= 0 AND commission_percentage <= 100",
            name="commission_percentage",
        ),
        sa.CheckConstraint(
            "commission_amount >= 0",
            name="commission_amount_non_negative",
        ),
        sa.ForeignKeyConstraint(
            ["appointment_id"],
            ["appointments.id"],
            name="fk_commissions_appointment_id_appointments",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["staff_id"],
            ["staff.id"],
            name="fk_commissions_staff_id_staff",
            ondelete="RESTRICT",
        ),
    )
    _mixin_indexes("commissions", branch=True)
    op.create_index("ix_commissions_staff_id", "commissions", ["staff_id"])
    op.create_index(
        "ix_commissions_staff_created_at",
        "commissions",
        ["staff_id", "created_at"],
    )
    op.create_index(
        "uq_commissions_appointment_id_active",
        "commissions",
        ["appointment_id"],
        unique=True,
        postgresql_where=ACTIVE_ROW,
    )

    op.create_table(
        "tips",
        sa.Column("appointment_id", sa.Uuid(), nullable=False),
        sa.Column("staff_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        *_base_columns(branch=True),
        sa.PrimaryKeyConstraint("id", name="pk_tips"),
        sa.CheckConstraint("amount > 0", name="amount_positive"),
        sa.ForeignKeyConstraint(
            ["appointment_id"],
            ["appointments.id"],
            name="fk_tips_appointment_id_appointments",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["staff_id"],
            ["staff.id"],
            name="fk_tips_staff_id_staff",
            ondelete="RESTRICT",
        ),
    )
    _mixin_indexes("tips", branch=True)
    op.create_index("ix_tips_appointment_id", "tips", ["appointment_id"])
    op.create_index("ix_tips_staff_id", "tips", ["staff_id"])
    op.create_index("ix_tips_staff_created_at", "tips", ["staff_id", "created_at"])

    op.create_table(
        "tasks",
        sa.Column("assigned_staff_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *_base_columns(branch=True),
        sa.PrimaryKeyConstraint("id", name="pk_tasks"),
        sa.CheckConstraint(
            "status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED')",
            name="status_allowed",
        ),
        sa.CheckConstraint(
            "(status <> 'COMPLETED') OR (completed_at IS NOT NULL)",
            name="completed_requires_completed_at",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_staff_id"],
            ["staff.id"],
            name="fk_tasks_assigned_staff_id_staff",
            ondelete="RESTRICT",
        ),
    )
    _mixin_indexes("tasks", branch=True)
    op.create_index(
        "ix_tasks_assigned_staff_status",
        "tasks",
        ["assigned_staff_id", "status"],
    )
    op.create_index("ix_tasks_due_date", "tasks", ["due_date"])


def downgrade() -> None:
    op.drop_table("tasks")
    op.drop_table("tips")
    op.drop_table("commissions")
    op.drop_table("payments")
    op.drop_table("invoices")
    op.drop_table("appointment_services")
    op.drop_table("appointments")
    op.drop_table("staff_schedules")
    op.drop_table("customers")
    op.drop_table("services")
    op.drop_table("staff")
    op.drop_table("refresh_tokens")
    op.drop_table("user_roles")
    op.drop_table("users")
    op.drop_table("roles")
