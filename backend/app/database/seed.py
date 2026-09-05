"""Idempotent V1 database seeders. Run with `python -m app.database.seed` from backend/."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import Role as RoleName
from app.common.enums import StaffStatus
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, get_logger
from app.core.security import hash_password
from app.database import models as _models  # noqa: F401
from app.database.session import async_session_maker, engine
from app.services.models import Service
from app.schedules.models import StaffSchedule
from app.staff.models import Staff
from app.users.models import Role, User, UserRole

logger = get_logger(__name__)

DEFAULT_ADMIN_PASSWORD = "AdminPass123!"
DEFAULT_STAFF_PASSWORD = "StaffPass123!"


@dataclass(frozen=True)
class SampleServiceSpec:
    name: str
    description: str
    category: str
    duration_minutes: int
    price: Decimal


@dataclass(frozen=True)
class SampleStaffSpec:
    name: str
    email: str
    phone: str
    designation: str
    commission_percentage: Decimal
    joining_date: date


SAMPLE_SERVICES: tuple[SampleServiceSpec, ...] = (
    SampleServiceSpec(
        name="Hair cutting",
        description="Precision haircut with wash and finish",
        category="Hair",
        duration_minutes=30,
        price=Decimal("25.00"),
    ),
    SampleServiceSpec(
        name="Beard setting with steam",
        description="Beard shape and set with a hot steam finish",
        category="Beard",
        duration_minutes=30,
        price=Decimal("25.00"),
    ),
    SampleServiceSpec(
        name="Face scrub",
        description="Exfoliating face scrub for a clean, fresh finish",
        category="Facial",
        duration_minutes=30,
        price=Decimal("30.00"),
    ),
    SampleServiceSpec(
        name="Keratin",
        description="Smoothing keratin treatment for frizz control and shine",
        category="Hair",
        duration_minutes=90,
        price=Decimal("120.00"),
    ),
    SampleServiceSpec(
        name="Hair spa",
        description="Nourishing hair spa treatment",
        category="Spa",
        duration_minutes=45,
        price=Decimal("60.00"),
    ),
    SampleServiceSpec(
        name="Dye",
        description="Hair dye application and rinse",
        category="Color",
        duration_minutes=45,
        price=Decimal("35.00"),
    ),
    SampleServiceSpec(
        name="Beard colouring",
        description="Beard colour blend and finish",
        category="Beard",
        duration_minutes=25,
        price=Decimal("25.00"),
    ),
    SampleServiceSpec(
        name="Normal Facial",
        description="Classic cleansing facial for all skin types",
        category="Facial",
        duration_minutes=60,
        price=Decimal("90.00"),
    ),
    SampleServiceSpec(
        name="Hydra facial",
        description="Hydrating facial with deep cleanse and serum infusion",
        category="Facial",
        duration_minutes=75,
        price=Decimal("150.00"),
    ),
    SampleServiceSpec(
        name="Special facial",
        description="Premium facial with extended treatment and finish",
        category="Facial",
        duration_minutes=90,
        price=Decimal("200.00"),
    ),
    SampleServiceSpec(
        name="Cleanup",
        description="Skin cleanup with extraction and tone",
        category="Facial",
        duration_minutes=45,
        price=Decimal("60.00"),
    ),
    SampleServiceSpec(
        name="Face wax",
        description="Face waxing for a clean, smooth finish",
        category="Facial",
        duration_minutes=20,
        price=Decimal("35.00"),
    ),
    SampleServiceSpec(
        name="Oil massage",
        description="Relaxing oil massage for scalp and shoulders",
        category="Spa",
        duration_minutes=30,
        price=Decimal("30.00"),
    ),
)

SAMPLE_STAFF: tuple[SampleStaffSpec, ...] = (
    SampleStaffSpec(
        name="Priya Sharma",
        email="priya@example.com",
        phone="9876500001",
        designation="Senior Stylist",
        commission_percentage=Decimal("40.00"),
        joining_date=date(2024, 1, 15),
    ),
    SampleStaffSpec(
        name="Rohan Mehta",
        email="rohan@example.com",
        phone="9876500002",
        designation="Barber",
        commission_percentage=Decimal("35.00"),
        joining_date=date(2024, 3, 1),
    ),
    SampleStaffSpec(
        name="Ananya Iyer",
        email="ananya@example.com",
        phone="9876500003",
        designation="Colorist",
        commission_percentage=Decimal("40.00"),
        joining_date=date(2024, 6, 10),
    ),
)

# day_of_week: 0 = Monday … 6 = Sunday (matches availability engine)
# 12:00–23:59 represents shop hours 12:00 PM through midnight (12:00 AM).
DEFAULT_WORKING_DAYS: tuple[tuple[int, time, time], ...] = (
    (0, time(12, 0), time(23, 59)),
    (1, time(12, 0), time(23, 59)),
    (2, time(12, 0), time(23, 59)),
    (3, time(12, 0), time(23, 59)),
    (4, time(12, 0), time(23, 59)),
    (5, time(12, 0), time(23, 59)),
    (6, time(12, 0), time(23, 59)),
)


async def _active_role(session: AsyncSession, name: RoleName) -> Role | None:
    result = await session.execute(
        select(Role).where(Role.name == name, Role.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()


async def _active_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(
        select(User).where(func.lower(User.email) == email.lower(), User.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()


async def _active_user_role(session: AsyncSession, user_id: UUID, role_id: UUID) -> UserRole | None:
    result = await session.execute(
        select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
            UserRole.is_deleted.is_(False),
        )
    )
    return result.scalar_one_or_none()


async def _assign_role(session: AsyncSession, user: User, role: Role) -> bool:
    existing = await _active_user_role(session, user.id, role.id)
    if existing is not None:
        return False
    session.add(UserRole(user_id=user.id, role_id=role.id))
    await session.flush()
    return True


async def seed_roles(session: AsyncSession) -> dict[RoleName, Role]:
    """Ensure ADMIN, RECEPTIONIST, and STAFF roles exist."""
    roles: dict[RoleName, Role] = {}
    created = 0
    for name in RoleName:
        role = await _active_role(session, name)
        if role is None:
            role = Role(name=name)
            session.add(role)
            await session.flush()
            created += 1
        roles[name] = role
    logger.info("seeded_roles", created=created, skipped=len(RoleName) - created)
    return roles


async def seed_admin_user(
    session: AsyncSession,
    roles: dict[RoleName, Role],
    *,
    name: str,
    email: str,
    password: str,
) -> User:
    """Ensure one active admin user exists and is linked to ADMIN."""
    user = await _active_user_by_email(session, email)
    created = False
    if user is None:
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            is_active=True,
        )
        session.add(user)
        await session.flush()
        created = True
    assigned = await _assign_role(session, user, roles[RoleName.ADMIN])
    logger.info("seeded_admin_user", email=email, created=created, role_assigned=assigned)
    return user


async def seed_sample_services(session: AsyncSession) -> list[Service]:
    """Ensure the sample salon catalog exists."""
    services: list[Service] = []
    created = 0
    for spec in SAMPLE_SERVICES:
        result = await session.execute(
            select(Service).where(
                func.lower(Service.name) == spec.name.lower(),
                Service.is_deleted.is_(False),
            )
        )
        service = result.scalar_one_or_none()
        if service is None:
            service = Service(
                name=spec.name,
                description=spec.description,
                category=spec.category,
                duration_minutes=spec.duration_minutes,
                price=spec.price,
                is_active=True,
            )
            session.add(service)
            await session.flush()
            created += 1
        else:
            service.description = spec.description
            service.category = spec.category
            service.duration_minutes = spec.duration_minutes
            service.price = spec.price
            service.is_active = True
        services.append(service)
    logger.info("seeded_sample_services", created=created, skipped=len(SAMPLE_SERVICES) - created)
    return services


async def seed_sample_staff(
    session: AsyncSession,
    roles: dict[RoleName, Role],
    *,
    password: str,
) -> list[Staff]:
    """Ensure sample staff users, STAFF roles, and staff profiles exist."""
    staff_members: list[Staff] = []
    created = 0
    staff_role = roles[RoleName.STAFF]
    for spec in SAMPLE_STAFF:
        user = await _active_user_by_email(session, spec.email)
        if user is None:
            user = User(
                name=spec.name,
                email=spec.email,
                password_hash=hash_password(password),
                is_active=True,
            )
            session.add(user)
            await session.flush()
        await _assign_role(session, user, staff_role)

        result = await session.execute(
            select(Staff).where(Staff.phone == spec.phone, Staff.is_deleted.is_(False))
        )
        staff = result.scalar_one_or_none()
        if staff is None:
            result = await session.execute(
                select(Staff).where(Staff.user_id == user.id, Staff.is_deleted.is_(False))
            )
            staff = result.scalar_one_or_none()
        if staff is None:
            staff = Staff(
                user_id=user.id,
                name=spec.name,
                phone=spec.phone,
                designation=spec.designation,
                commission_percentage=spec.commission_percentage,
                joining_date=spec.joining_date,
                status=StaffStatus.ACTIVE,
            )
            session.add(staff)
            await session.flush()
            created += 1
        staff_members.append(staff)
    logger.info("seeded_sample_staff", created=created, skipped=len(SAMPLE_STAFF) - created)
    return staff_members


async def seed_sample_schedules(session: AsyncSession, staff_members: list[Staff]) -> None:
    """Ensure default weekly working hours exist for sample staff."""
    created = 0
    updated = 0
    for staff in staff_members:
        for day_of_week, start_time, end_time in DEFAULT_WORKING_DAYS:
            result = await session.execute(
                select(StaffSchedule).where(
                    StaffSchedule.staff_id == staff.id,
                    StaffSchedule.day_of_week == day_of_week,
                    StaffSchedule.is_deleted.is_(False),
                )
            )
            existing = result.scalar_one_or_none()
            if existing is not None:
                if existing.start_time != start_time or existing.end_time != end_time:
                    existing.start_time = start_time
                    existing.end_time = end_time
                    updated += 1
                continue
            session.add(
                StaffSchedule(
                    staff_id=staff.id,
                    day_of_week=day_of_week,
                    start_time=start_time,
                    end_time=end_time,
                )
            )
            created += 1
            await session.flush()
    logger.info("seeded_sample_schedules", created=created, updated=updated)


def _reject_default_passwords_in_production(settings: Settings) -> None:
    if not settings.is_production:
        return
    if settings.SEED_ADMIN_PASSWORD == DEFAULT_ADMIN_PASSWORD:
        raise ValueError("SEED_ADMIN_PASSWORD must be set to a unique secret in production")
    if settings.SEED_STAFF_PASSWORD == DEFAULT_STAFF_PASSWORD:
        raise ValueError("SEED_STAFF_PASSWORD must be set to a unique secret in production")


async def seed_database(session: AsyncSession, settings: Settings | None = None) -> None:
    """Run all V1 seeders. Safe to re-run."""
    active_settings = settings or get_settings()
    _reject_default_passwords_in_production(active_settings)

    roles = await seed_roles(session)
    await seed_admin_user(
        session,
        roles,
        name=active_settings.SEED_ADMIN_NAME,
        email=active_settings.SEED_ADMIN_EMAIL,
        password=active_settings.SEED_ADMIN_PASSWORD,
    )
    await seed_sample_services(session)
    staff_members = await seed_sample_staff(session, roles, password=active_settings.SEED_STAFF_PASSWORD)
    await seed_sample_schedules(session, staff_members)
    logger.info("database_seed_complete")


async def _run() -> None:
    settings = get_settings()
    configure_logging(settings)
    async with async_session_maker() as session:
        try:
            await seed_database(session, settings)
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await engine.dispose()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
