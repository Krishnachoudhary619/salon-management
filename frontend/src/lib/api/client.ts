import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

import { env } from "@/config/env";
import { apiEndpoints } from "@/config/routes";
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "@/lib/auth/token-storage";
import type { ApiErrorResponse, ApiResponse, RefreshTokenRequest, TokenResponse } from "@/types/api";

import { ApiError, isApiErrorResponse, normalizeAxiosError } from "./errors";

type RetriableConfig = InternalAxiosRequestConfig & { _retry?: boolean };

let refreshPromise: Promise<string | null> | null = null;
let onUnauthorized: (() => void) | null = null;

export function registerUnauthorizedHandler(handler: () => void) {
  onUnauthorized = handler;
}

export const apiClient = axios.create({
  baseURL: env.NEXT_PUBLIC_API_BASE_URL,
  headers: {
    Accept: "application/json",
    "Content-Type": "application/json",
  },
  timeout: 30_000,
});

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorResponse>) => {
    const config = error.config as RetriableConfig | undefined;
    const status = error.response?.status;

    if (status === 401 && config && !config._retry && !isAuthRoute(config.url)) {
      config._retry = true;
      const nextToken = await refreshAccessToken();
      if (nextToken) {
        config.headers.Authorization = `Bearer ${nextToken}`;
        return apiClient(config);
      }
      clearTokens();
      onUnauthorized?.();
    }

    return Promise.reject(normalizeAxiosError(error));
  },
);

function isAuthRoute(url: string | undefined): boolean {
  if (!url) {
    return false;
  }
  return url.includes(apiEndpoints.auth.login) || url.includes(apiEndpoints.auth.refresh);
}

async function refreshAccessToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = performRefresh().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

async function performRefresh(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    return null;
  }

  try {
    const payload: RefreshTokenRequest = { refresh_token: refreshToken };
    const response = await axios.post<ApiResponse<TokenResponse>>(
      `${env.NEXT_PUBLIC_API_BASE_URL}${apiEndpoints.auth.refresh}`,
      payload,
      {
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
      },
    );

    const data = response.data.data;
    if (!response.data.success || !data) {
      return null;
    }

    setTokens(data.access_token, data.refresh_token);
    return data.access_token;
  } catch {
    return null;
  }
}

export async function apiRequest<T>(
  request: () => Promise<{ data: ApiResponse<T> }>,
): Promise<T> {
  const response = await request();
  if (!response.data.success) {
    throw new ApiError(response.data.message, {
      status: 400,
      errors: isApiErrorResponse(response.data) ? response.data.errors : [],
    });
  }
  if (response.data.data === null || response.data.data === undefined) {
    throw new ApiError("Empty response from server", { status: 500 });
  }
  return response.data.data;
}

export async function apiRequestOptional<T>(
  request: () => Promise<{ data: ApiResponse<T> }>,
): Promise<T | null> {
  const response = await request();
  if (!response.data.success) {
    throw new ApiError(response.data.message, {
      status: 400,
      errors: isApiErrorResponse(response.data) ? response.data.errors : [],
    });
  }
  return response.data.data ?? null;
}
