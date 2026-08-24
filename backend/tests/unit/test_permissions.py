from uuid import uuid4

import pytest

from app.common.enums import Permission, Role
from app.core.exceptions import PermissionDeniedException
from app.core.permissions import (
    ensure_owner_or_admin,
    get_permissions_for_roles,
    has_any_permission,
    has_permission,
)
from app.core.security import CurrentUser


def _user(*roles: Role) -> CurrentUser:
    return CurrentUser(id=uuid4(), roles=list(roles), email="user@salon.test")


def test_admin_has_every_permission() -> None:
    admin = _user(Role.ADMIN)
    for permission in Permission:
        assert has_permission(admin, permission)


def test_receptionist_can_manage_front_desk_but_not_reports() -> None:
    receptionist = _user(Role.RECEPTIONIST)
    assert has_permission(receptionist, Permission.CUSTOMER_READ, Permission.APPOINTMENT_WRITE)
    assert has_permission(receptionist, Permission.SCHEDULE_READ)
    assert not has_permission(receptionist, Permission.REPORTS_READ)
    assert not has_permission(receptionist, Permission.COMMISSION_CONFIG)
    assert not has_permission(receptionist, Permission.DASHBOARD_READ)
    assert not has_permission(receptionist, Permission.STAFF_WRITE)


def test_staff_can_access_own_records_only() -> None:
    staff = _user(Role.STAFF)
    assert has_permission(staff, Permission.APPOINTMENT_READ_OWN)
    assert has_permission(staff, Permission.COMMISSION_READ_OWN)
    assert has_permission(staff, Permission.TASK_READ_OWN)
    assert not has_permission(staff, Permission.CUSTOMER_READ)
    assert not has_permission(staff, Permission.STAFF_WRITE)
    assert not has_permission(staff, Permission.REPORTS_READ)
    assert has_any_permission(staff, Permission.CUSTOMER_READ, Permission.TASK_READ_OWN)


def test_ensure_owner_or_admin() -> None:
    owner_id = uuid4()
    owner = CurrentUser(id=owner_id, roles=[Role.STAFF])
    other = CurrentUser(id=uuid4(), roles=[Role.STAFF])
    admin = CurrentUser(id=uuid4(), roles=[Role.ADMIN])

    ensure_owner_or_admin(owner, owner_id)
    ensure_owner_or_admin(admin, owner_id)
    with pytest.raises(PermissionDeniedException):
        ensure_owner_or_admin(other, owner_id)


def test_combined_roles_union_permissions() -> None:
    granted = get_permissions_for_roles([Role.STAFF, Role.RECEPTIONIST])
    assert Permission.CUSTOMER_READ in granted
    assert Permission.TASK_READ_OWN in granted
    assert Permission.COMMISSION_CONFIG not in granted
