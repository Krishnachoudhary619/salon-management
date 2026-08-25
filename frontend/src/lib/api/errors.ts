import type { AxiosError } from "axios";

import type { ApiErrorItem, ApiErrorResponse } from "@/types/api";

export class ApiError extends Error {
  readonly status: number;
  readonly errors: ApiErrorItem[];

  constructor(message: string, options: { status: number; errors?: ApiErrorItem[] }) {
    super(message);
    this.name = "ApiError";
    this.status = options.status;
    this.errors = options.errors ?? [];
  }
}

export function isApiErrorResponse(value: unknown): value is ApiErrorResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "success" in value &&
    (value as ApiErrorResponse).success === false &&
    "message" in value
  );
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

export function normalizeAxiosError(error: AxiosError<ApiErrorResponse>): ApiError {
  if (error.response?.data && isApiErrorResponse(error.response.data)) {
    return new ApiError(error.response.data.message, {
      status: error.response.status ?? 400,
      errors: error.response.data.errors,
    });
  }

  if (error.code === "ECONNABORTED") {
    return new ApiError("Request timed out. Please try again.", { status: 408 });
  }

  if (!error.response) {
    return new ApiError("Network error. Check your connection and try again.", {
      status: 0,
    });
  }

  return new ApiError(error.message || "Request failed", {
    status: error.response.status,
  });
}

export function getErrorMessage(error: unknown, fallback = "Something went wrong"): string {
  if (isApiError(error)) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return fallback;
}

export function getFieldErrors(error: unknown): Record<string, string> {
  if (!isApiError(error)) {
    return {};
  }
  return error.errors.reduce<Record<string, string>>((acc, item) => {
    if (item.field) {
      acc[item.field] = item.message;
    }
    return acc;
  }, {});
}
