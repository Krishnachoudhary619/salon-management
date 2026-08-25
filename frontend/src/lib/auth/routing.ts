import { adminNavItems } from "@/config/navigation";
import { roleHomeRoutes, defaultAuthenticatedRoute } from "@/config/routes";
import {
  hasAllPermissions,
  hasAnyPermission,
} from "@/lib/auth/permissions";
import type { Role } from "@/types/api";

export function isActivePath(pathname: string, href: string) {
  if (href === "/") {
    return pathname === "/";
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

function isNavItemAccessible(roles: Role[], item: (typeof adminNavItems)[number]) {
  if (item.anyPermission) {
    return hasAnyPermission(roles, [...item.permissions]);
  }
  return hasAllPermissions(roles, [...item.permissions]);
}

export function canAccessPath(roles: Role[], pathname: string): boolean {
  const item = adminNavItems.find((navItem) => isActivePath(pathname, navItem.href));
  if (!item) {
    return true;
  }
  return isNavItemAccessible(roles, item);
}

export function getFirstAccessibleRoute(roles: Role[]): string {
  const accessible = adminNavItems.find((item) => isNavItemAccessible(roles, item));
  return accessible?.href ?? defaultAuthenticatedRoute;
}

export function getRoleHomeRoute(roles: Role[]): string {
  const preferred =
    roles.includes("ADMIN")
      ? roleHomeRoutes.ADMIN
      : roles.includes("RECEPTIONIST")
        ? roleHomeRoutes.RECEPTIONIST
        : roles.includes("STAFF")
          ? roleHomeRoutes.STAFF
          : defaultAuthenticatedRoute;

  if (canAccessPath(roles, preferred)) {
    return preferred;
  }

  return getFirstAccessibleRoute(roles);
}

export function getPrimaryRole(roles: Role[]): Role | null {
  if (roles.includes("ADMIN")) {
    return "ADMIN";
  }
  if (roles.includes("RECEPTIONIST")) {
    return "RECEPTIONIST";
  }
  if (roles.includes("STAFF")) {
    return "STAFF";
  }
  return null;
}
