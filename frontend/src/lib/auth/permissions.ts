import type { Permission, Role } from "@/types/api";

/** Mirrors backend `ROLE_PERMISSIONS` in app/core/permissions.py */
export const ROLE_PERMISSIONS: Record<Role, readonly Permission[]> = {
  ADMIN: [
    "users:read",
    "users:write",
    "staff:read",
    "staff:write",
    "staff:delete",
    "services:read",
    "services:write",
    "services:delete",
    "customers:read",
    "customers:write",
    "schedules:read",
    "schedules:write",
    "appointments:read",
    "appointments:read_own",
    "appointments:write",
    "appointments:write_own",
    "payments:read",
    "payments:write",
    "invoices:read",
    "commissions:read",
    "commissions:read_own",
    "commissions:config",
    "tips:read",
    "tips:read_own",
    "tips:write",
    "tasks:read",
    "tasks:read_own",
    "tasks:write",
    "tasks:write_own",
    "dashboard:read",
    "reports:read",
    "performance:read",
    "performance:read_own",
  ],
  RECEPTIONIST: [
    "services:read",
    "customers:read",
    "customers:write",
    "schedules:read",
    "schedules:write",
    "appointments:read",
    "appointments:write",
    "payments:read",
    "payments:write",
    "invoices:read",
    "tips:read",
    "tips:write",
  ],
  STAFF: [
    "services:read",
    "appointments:read_own",
    "appointments:write_own",
    "commissions:read_own",
    "tips:read_own",
    "tasks:read_own",
    "tasks:write_own",
    "performance:read_own",
  ],
};

export function getPermissionsForRoles(roles: Role[]): Set<Permission> {
  const granted = new Set<Permission>();
  for (const role of roles) {
    for (const permission of ROLE_PERMISSIONS[role] ?? []) {
      granted.add(permission);
    }
  }
  return granted;
}

export function hasRole(roles: Role[], ...required: Role[]): boolean {
  return required.some((role) => roles.includes(role));
}

export function hasPermission(
  roles: Role[],
  permission: Permission,
  granted?: Set<Permission>,
): boolean {
  const permissions = granted ?? getPermissionsForRoles(roles);
  return permissions.has(permission);
}

export function hasAnyPermission(
  roles: Role[],
  required: Permission[],
  granted?: Set<Permission>,
): boolean {
  const permissions = granted ?? getPermissionsForRoles(roles);
  return required.some((permission) => permissions.has(permission));
}

export function hasAllPermissions(
  roles: Role[],
  required: Permission[],
  granted?: Set<Permission>,
): boolean {
  const permissions = granted ?? getPermissionsForRoles(roles);
  return required.every((permission) => permissions.has(permission));
}

export function isAdmin(roles: Role[]): boolean {
  return hasRole(roles, "ADMIN");
}
