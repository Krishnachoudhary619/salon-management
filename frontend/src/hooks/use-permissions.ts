"use client";

import { useMemo } from "react";

import { useAuth } from "@/hooks/use-auth";
import {
  getPermissionsForRoles,
  hasAllPermissions,
  hasAnyPermission,
  hasPermission,
  hasRole,
  isAdmin,
} from "@/lib/auth/permissions";
import type { Permission, Role } from "@/types/api";

export function usePermissions() {
  const { user } = useAuth();

  return useMemo(() => {
    const roles = user?.roles ?? [];
    const granted = getPermissionsForRoles(roles);

    return {
      roles,
      permissions: granted,
      isAdmin: isAdmin(roles),
      hasRole: (...required: Role[]) => hasRole(roles, ...required),
      can: (permission: Permission | Permission[]) => {
        const required = Array.isArray(permission) ? permission : [permission];
        return hasAllPermissions(roles, required, granted);
      },
      canAny: (required: Permission[]) => hasAnyPermission(roles, required, granted),
      canOne: (permission: Permission) => hasPermission(roles, permission, granted),
    };
  }, [user]);
}
