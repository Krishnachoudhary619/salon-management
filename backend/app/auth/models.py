from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel, restrict_fk

if TYPE_CHECKING:
    from app.users.models import User


class RefreshToken(BaseModel):
    """Persisted refresh token for rotation and logout."""

    __tablename__ = "refresh_tokens"

    user_id: Mapped[UUID] = mapped_column(restrict_fk("users.id"), nullable=False)
    jti: Mapped[UUID] = mapped_column(nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replaced_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("refresh_tokens.id", ondelete="SET NULL"),
        nullable=True,
    )

    user: Mapped[User] = relationship(back_populates="refresh_tokens")
    replaced_by: Mapped[RefreshToken | None] = relationship(
        remote_side="RefreshToken.id",
        foreign_keys="RefreshToken.replaced_by_id",
        uselist=False,
    )

    __table_args__ = (
        UniqueConstraint("jti", name="uq_refresh_tokens_jti"),
        UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
        Index("ix_refresh_tokens_user_revoked_expires", "user_id", "revoked_at", "expires_at"),
        Index("ix_refresh_tokens_expires_at", "expires_at"),
    )
