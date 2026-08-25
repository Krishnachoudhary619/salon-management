import { apiClient, apiRequest, apiRequestOptional } from "@/lib/api/client";
import { apiEndpoints } from "@/config/routes";
import type { AuthUser, LoginRequest, TokenResponse } from "@/types/api";

export async function login(payload: LoginRequest): Promise<TokenResponse> {
  return apiRequest(() => apiClient.post(apiEndpoints.auth.login, payload));
}

export async function fetchCurrentUser(): Promise<AuthUser> {
  return apiRequest(() => apiClient.get(apiEndpoints.auth.me));
}

export async function logout(): Promise<void> {
  await apiRequestOptional(() => apiClient.post(apiEndpoints.auth.logout));
}
