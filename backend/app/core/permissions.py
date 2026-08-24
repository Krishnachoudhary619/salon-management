from collections.abc import Callable
from uuid import UUID

from fastapi import Depends

from app.common.enums import Permission, Role
from app.core.exceptions import PermissionDeniedException
from app.core.security import CurrentUser

ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ADMIN: frozenset(Permission),
    Role.RECEPTIONIST: frozenset(
        {
            Permission.SERVICE_READ,
            Permission.CUSTOMER_READ,
            Permission.CUSTOMER_WRITE,
            Permission.SCHEDULE_READ,
            Permission.SCHEDULE_WRITE,
            Permission.APPOINTMENT_READ,
            Permission.APPOINTMENT_WRITE,
            Permission.PAYMENT_READ,
            Permission.PAYMENT_WRITE,
            Permission.INVOICE_READ,
            Permission.TIP_READ,
            Permission.TIP_WRITE,
        }
    ),
    Role.STAFF: frozenset(
        {
            Permission.SERVICE_READ,
            Permission.APPOINTMENT_READ_OWN,
            Permission.APPOINTMENT_WRITE_OWN,
            Permission.COMMISSION_READ_OWN,
            Permission.TIP_READ_OWN,
            Permission.TASK_READ_OWN,
            Permission.TASK_WRITE_OWN,
            Permission.PERFORMANCE_READ_OWN,
        }
    ),
}


def get_permissions_for_roles(roles: list[Role]) -> set[Permission]:
    granted: set[Permission] = set()
    for role in roles:
        granted.update(ROLE_PERMISSIONS.get(role, frozenset()))
    return granted


def has_permission(user: CurrentUser, *permissions: Permission) -> bool:
    granted = get_permissions_for_roles(user.roles)
    return all(permission in granted for permission in permissions)


def has_any_permission(user: CurrentUser, *permissions: Permission) -> bool:
    granted = get_permissions_for_roles(user.roles)
    return any(permission in granted for permission in permissions)


def ensure_owner_or_admin(user: CurrentUser, resource_owner_id: UUID) -> None:
    """Allow access when the caller is ADMIN or owns the resource."""
    if user.is_admin or user.id == resource_owner_id:
        return
    raise PermissionDeniedException("You can only access your own records")


def require_roles(*roles: Role) -> Callable[..., CurrentUser]:
    """FastAPI dependency that requires the caller to have at least one role."""
    from app.common.dependencies import get_current_user

    async def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not current_user.has_role(*roles):
            raise PermissionDeniedException()
        return current_user

    return dependency


def require_permissions(
    *permissions: Permission,
    any_of: bool = False,
) -> Callable[..., CurrentUser]:
    """FastAPI dependency that enforces the RBAC permission matrix."""
    from app.common.dependencies import get_current_user

    async def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        allowed = (
            has_any_permission(current_user, *permissions)
            if any_of
            else has_permission(current_user, *permissions)
        )
        if not allowed:
            raise PermissionDeniedException()
        return current_user

    return dependency
