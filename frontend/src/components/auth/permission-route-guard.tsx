"use client";

import { useEffect, type ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";

import { FullPageLoader } from "@/components/feedback/loading-state";
import { useAuth } from "@/hooks/use-auth";
import { canAccessPath, getRoleHomeRoute } from "@/lib/auth/routing";

interface PermissionRouteGuardProps {
  children: ReactNode;
}

/** Redirects users away from routes their role cannot access. */
export function PermissionRouteGuard({ children }: PermissionRouteGuardProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated, isBootstrapping } = useAuth();

  const allowed = user ? canAccessPath(user.roles, pathname) : true;

  useEffect(() => {
    if (!isBootstrapping && isAuthenticated && user && !allowed) {
      router.replace(getRoleHomeRoute(user.roles));
    }
  }, [allowed, isAuthenticated, isBootstrapping, pathname, router, user]);

  if (isBootstrapping) {
    return <FullPageLoader label="Checking session" />;
  }

  if (user && !allowed) {
    return <FullPageLoader label="Redirecting" />;
  }

  return children;
}
