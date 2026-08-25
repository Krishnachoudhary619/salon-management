"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";

import { FullPageLoader } from "@/components/feedback/loading-state";
import { useAuth } from "@/hooks/use-auth";
import {
  hasAllPermissions,
  hasAnyPermission,
  hasRole,
} from "@/lib/auth/permissions";
import type { Permission, Role } from "@/types/api";

interface RouteGuardProps {
  children: ReactNode;
  roles?: Role[];
  permissions?: Permission[];
  anyPermission?: boolean;
  redirectTo?: string;
  fallback?: ReactNode;
}

/** Redirects unauthenticated users and optionally enforces roles or permissions. */
export function RouteGuard({
  children,
  roles,
  permissions,
  anyPermission = false,
  redirectTo = "/login",
  fallback = null,
}: RouteGuardProps) {
  const router = useRouter();
  const { user, isAuthenticated, isBootstrapping } = useAuth();

  useEffect(() => {
    if (!isBootstrapping && !isAuthenticated) {
      router.replace(redirectTo);
    }
  }, [isAuthenticated, isBootstrapping, redirectTo, router]);

  if (isBootstrapping) {
    return <FullPageLoader label="Checking session" />;
  }

  if (!isAuthenticated || !user) {
    return null;
  }

  if (roles && !hasRole(user.roles, ...roles)) {
    return fallback;
  }

  if (permissions?.length) {
    const allowed = anyPermission
      ? hasAnyPermission(user.roles, permissions)
      : hasAllPermissions(user.roles, permissions);
    if (!allowed) {
      return fallback;
    }
  }

  return children;
}
