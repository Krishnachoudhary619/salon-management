"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { fetchCurrentUser, login as loginRequest, logout as logoutRequest } from "@/lib/api/auth";
import { registerUnauthorizedHandler } from "@/lib/api/client";
import { clearTokens, hasStoredSession, setTokens } from "@/lib/auth/token-storage";
import { toast } from "@/lib/toast";
import { queryKeys } from "@/config/query-client";
import type { AuthUser, LoginRequest } from "@/types/api";

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isBootstrapping: boolean;
  login: (payload: LoginRequest) => Promise<AuthUser>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const router = useRouter();
  const [sessionEnabled, setSessionEnabled] = useState(false);

  useEffect(() => {
    setSessionEnabled(hasStoredSession());
  }, []);

  useEffect(() => {
    registerUnauthorizedHandler(() => {
      clearTokens();
      setSessionEnabled(false);
      queryClient.clear();
      router.replace("/login");
      toast.error("Your session expired. Please sign in again.");
    });
  }, [queryClient, router]);

  const meQuery = useQuery({
    queryKey: queryKeys.auth.me,
    queryFn: fetchCurrentUser,
    enabled: sessionEnabled,
    retry: false,
  });

  useEffect(() => {
    if (meQuery.isError) {
      clearTokens();
      setSessionEnabled(false);
      queryClient.removeQueries({ queryKey: queryKeys.auth.me });
    }
  }, [meQuery.isError, queryClient]);

  const loginMutation = useMutation({
    mutationFn: loginRequest,
    onSuccess: (data) => {
      setTokens(data.access_token, data.refresh_token);
      setSessionEnabled(true);
      queryClient.setQueryData(queryKeys.auth.me, data.user);
    },
  });

  const logoutMutation = useMutation({
    mutationFn: logoutRequest,
  });

  const login = useCallback(
    async (payload: LoginRequest) => {
      const data = await loginMutation.mutateAsync(payload);
      return data.user;
    },
    [loginMutation],
  );

  const logout = useCallback(async () => {
    try {
      await logoutMutation.mutateAsync();
    } catch {
      // Local session is cleared even when the API call fails.
    } finally {
      clearTokens();
      setSessionEnabled(false);
      queryClient.clear();
    }
  }, [logoutMutation, queryClient]);

  const refreshUser = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.auth.me });
  }, [queryClient]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user: meQuery.data ?? null,
      isAuthenticated: Boolean(meQuery.data),
      isLoading:
        loginMutation.isPending ||
        logoutMutation.isPending ||
        (sessionEnabled && meQuery.isFetching),
      isBootstrapping: sessionEnabled && meQuery.isLoading,
      login,
      logout,
      refreshUser,
    }),
    [
      login,
      loginMutation.isPending,
      logout,
      logoutMutation.isPending,
      meQuery.data,
      meQuery.isFetching,
      meQuery.isLoading,
      refreshUser,
      sessionEnabled,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuthContext must be used within AuthProvider");
  }
  return context;
}
