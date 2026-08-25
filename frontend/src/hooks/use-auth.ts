"use client";

import { useAuthContext } from "@/components/auth/auth-provider";

export function useAuth() {
  return useAuthContext();
}

export function useRequireAuth(redirectTo = "/login") {
  const auth = useAuthContext();
  return {
    ...auth,
    redirectTo,
  };
}
