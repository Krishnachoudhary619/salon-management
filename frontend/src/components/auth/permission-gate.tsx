"use client";

import type { ReactNode } from "react";

import { usePermissions } from "@/hooks/use-permissions";
import type { Permission, Role } from "@/types/api";

interface PermissionGateProps {
  children: ReactNode;
  permissions: Permission[];
  any?: boolean;
  fallback?: ReactNode;
}

/** Renders children only when the current user has the required permissions. */
export function PermissionGate({
  children,
  permissions,
  any: anyPermission = false,
  fallback = null,
}: PermissionGateProps) {
  const { can, canAny } = usePermissions();
  const allowed = anyPermission ? canAny(permissions) : can(permissions);
  return allowed ? children : fallback;
}

interface RoleGateProps {
  children: ReactNode;
  roles: Role[];
  fallback?: ReactNode;
}

/** Renders children only when the current user has at least one required role. */
export function RoleGate({ children, roles, fallback = null }: RoleGateProps) {
  const { hasRole: userHasRole } = usePermissions();
  return userHasRole(...roles) ? children : fallback;
}
