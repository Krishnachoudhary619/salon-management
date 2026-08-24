from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Index, String, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import Role as RoleName
from app.database.base import (
    ACTIVE_ROW_SQL,
    BaseModel,
    check_allowed_values,
    restrict_fk,
)

if TYPE_CHECKING:
    from app.auth.models import RefreshToken
    from app.staff.models import Staff


class Role(BaseModel):
    """Closed set of RBAC roles. Seeded in V1; not user-managed."""

    __tablename__ = "roles"

    name: Mapped[RoleName] = mapped_column(String(32), nullable=False)

    user_roles: Mapped[list[UserRole]] = relationship(back_populates="role", lazy="selectin")

    __table_args__ = (
        check_allowed_values("name", tuple(item.value for item in RoleName), name="name_allowed"),
        Index(
            "uq_roles_name_active",
            "name",
            unique=True,
            postgresql_where=ACTIVE_ROW_SQL,
        ),
    )


class User(BaseModel):
    """Login identity for ADMIN, RECEPTIONIST, and STAFF. Customers are not users."""

    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true(),
    )

    user_roles: Mapped[list[UserRole]] = relationship(back_populates="user", lazy="selectin")
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="user",
        lazy="selectin",
    )
    staff: Mapped[Staff | None] = relationship(back_populates="user", uselist=False)

    __table_args__ = (
        Index(
            "uq_users_email_active",
            func.lower(email),
            unique=True,
            postgresql_where=ACTIVE_ROW_SQL,
        ),
        Index("ix_users_is_active", "is_active"),
    )


class UserRole(BaseModel):
    """Many-to-many assignment of roles to users."""

    __tablename__ = "user_roles"

    user_id: Mapped[UUID] = mapped_column(restrict_fk("users.id"), nullable=False)
    role_id: Mapped[UUID] = mapped_column(restrict_fk("roles.id"), nullable=False)

    user: Mapped[User] = relationship(back_populates="user_roles")
    role: Mapped[Role] = relationship(back_populates="user_roles")

    __table_args__ = (
        Index(
            "uq_user_roles_user_role_active",
            "user_id",
            "role_id",
            unique=True,
            postgresql_where=ACTIVE_ROW_SQL,
        ),
        Index("ix_user_roles_role_id", "role_id"),
    )
