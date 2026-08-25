"use client";

import { useCallback } from "react";

import { getErrorMessage } from "@/lib/api/errors";
import { toast } from "@/lib/toast";

export function useApiError() {
  const showError = useCallback((error: unknown, fallback = "Something went wrong") => {
    toast.error(getErrorMessage(error, fallback));
  }, []);

  return { showError };
}
