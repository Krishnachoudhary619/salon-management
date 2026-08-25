"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";

import { FullPageLoader } from "@/components/feedback/loading-state";
import { useAuth } from "@/hooks/use-auth";
import { getRoleHomeRoute } from "@/lib/auth/routing";

interface GuestGuardProps {
  children: ReactNode;
}

/** Keeps authenticated users off public pages such as login. */
export function GuestGuard({ children }: GuestGuardProps) {
  const router = useRouter();
  const { user, isAuthenticated, isBootstrapping } = useAuth();

  useEffect(() => {
    if (!isBootstrapping && isAuthenticated && user) {
      router.replace(getRoleHomeRoute(user.roles));
    }
  }, [isAuthenticated, isBootstrapping, router, user]);

  if (isBootstrapping) {
    return <FullPageLoader label="Checking session" />;
  }

  if (isAuthenticated) {
    return null;
  }

  return children;
}
