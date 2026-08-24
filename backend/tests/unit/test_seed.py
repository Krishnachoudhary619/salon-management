from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.common.enums import Role as RoleName
from app.common.enums import StaffStatus
from app.core.config import Settings
from app.core.security import verify_password
from app.database import models as _models  # noqa: F401
from app.database.base import Base
from app.database.seed import (
    SAMPLE_SERVICES,
    SAMPLE_STAFF,
    seed_database,
    seed_roles,
)
from app.services.models import Service
from app.staff.models import Staff
from app.users.models import Role, User, UserRole


@pytest.fixture
async def seed_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as session:
        yield session

    await engine.dispose()


def _settings() -> Settings:
    return Settings(
        APP_ENV="test",
        JWT_SECRET="unit-test-secret-key-must-be-32-chars",
        SEED_ADMIN_NAME="Salon Admin",
        SEED_ADMIN_EMAIL="admin@example.com",
        SEED_ADMIN_PASSWORD="AdminPass123!",
        SEED_STAFF_PASSWORD="StaffPass123!",
    )


async def test_seed_roles_are_idempotent(seed_session: AsyncSession) -> None:
    first = await seed_roles(seed_session)
    second = await seed_roles(seed_session)
    await seed_session.commit()

    assert set(first) == {RoleName.ADMIN, RoleName.RECEPTIONIST, RoleName.STAFF}
    assert {role.id for role in first.values()} == {role.id for role in second.values()}

    count = await seed_session.scalar(select(func.count()).select_from(Role))
    assert count == 3


async def test_seed_database_creates_admin_staff_and_services(seed_session: AsyncSession) -> None:
    await seed_database(seed_session, _settings())
    await seed_session.commit()

    admin = await seed_session.scalar(
        select(User).where(func.lower(User.email) == "admin@example.com")
    )
    assert admin is not None
    assert admin.name == "Salon Admin"
    assert admin.is_active is True
    assert verify_password("AdminPass123!", admin.password_hash) is True

    admin_role = await seed_session.scalar(select(Role).where(Role.name == RoleName.ADMIN))
    assert admin_role is not None
    link = await seed_session.scalar(
        select(UserRole).where(UserRole.user_id == admin.id, UserRole.role_id == admin_role.id)
    )
    assert link is not None

    service_count = await seed_session.scalar(select(func.count()).select_from(Service))
    staff_count = await seed_session.scalar(select(func.count()).select_from(Staff))
    assert service_count == len(SAMPLE_SERVICES)
    assert staff_count == len(SAMPLE_STAFF)

    staff = await seed_session.scalar(select(Staff).where(Staff.phone == "9876500001"))
    assert staff is not None
    assert staff.designation == "Senior Stylist"
    assert staff.status == StaffStatus.ACTIVE

    staff_user = await seed_session.get(User, staff.user_id)
    assert staff_user is not None
    assert verify_password("StaffPass123!", staff_user.password_hash) is True
    staff_role = await seed_session.scalar(select(Role).where(Role.name == RoleName.STAFF))
    assert staff_role is not None
    staff_link = await seed_session.scalar(
        select(UserRole).where(
            UserRole.user_id == staff_user.id,
            UserRole.role_id == staff_role.id,
        )
    )
    assert staff_link is not None


async def test_seed_database_is_idempotent(seed_session: AsyncSession) -> None:
    settings = _settings()
    await seed_database(seed_session, settings)
    await seed_session.commit()
    await seed_database(seed_session, settings)
    await seed_session.commit()

    assert await seed_session.scalar(select(func.count()).select_from(Role)) == 3
    user_count = await seed_session.scalar(select(func.count()).select_from(User))
    service_count = await seed_session.scalar(select(func.count()).select_from(Service))
    staff_count = await seed_session.scalar(select(func.count()).select_from(Staff))
    assert user_count == 1 + len(SAMPLE_STAFF)
    assert service_count == len(SAMPLE_SERVICES)
    assert staff_count == len(SAMPLE_STAFF)


async def test_production_seed_rejects_default_passwords(seed_session: AsyncSession) -> None:
    settings = Settings(
        APP_ENV="production",
        JWT_SECRET="a-unique-production-secret-key-value",
        CORS_ORIGINS="https://app.example.com",
        ALLOWED_HOSTS="api.example.com",
        DEBUG=False,
    )
    with pytest.raises(ValueError, match="SEED_ADMIN_PASSWORD"):
        await seed_database(seed_session, settings)
