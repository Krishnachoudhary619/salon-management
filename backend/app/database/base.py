from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, MetaData, false, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

ACTIVE_ROW_SQL = text("is_deleted = false")


def check_allowed_values(
    column_name: str,
    values: tuple[str, ...],
    *,
    name: str,
) -> CheckConstraint:
    quoted = ", ".join(f"'{value}'" for value in values)
    return CheckConstraint(f"{column_name} IN ({quoted})", name=name)


def restrict_fk(column: str) -> ForeignKey:
    return ForeignKey(column, ondelete="RESTRICT")


def utc_now() -> datetime:
    return datetime.now(UTC)


NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UUIDPrimaryKeyMixin:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)


class AuditMixin:
    """Created/updated timestamps and actor UUIDs required on every table."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        server_default=func.now(),
        nullable=False,
    )
    created_by: Mapped[UUID | None] = mapped_column(nullable=True)
    updated_by: Mapped[UUID | None] = mapped_column(nullable=True)


class SoftDeleteMixin:
    """Business records are never hard-deleted."""

    is_deleted: Mapped[bool] = mapped_column(
        default=False,
        server_default=false(),
        index=True,
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BranchAwareMixin:
    """Optional branch scoping reserved for future multi-branch support."""

    branch_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)


class BaseModel(Base, UUIDPrimaryKeyMixin, AuditMixin, SoftDeleteMixin):
    """Abstract model used by every business table."""

    __abstract__ = True


class BranchAwareModel(BaseModel, BranchAwareMixin):
    """Business table that is ready for future multi-branch scoping."""

    __abstract__ = True
