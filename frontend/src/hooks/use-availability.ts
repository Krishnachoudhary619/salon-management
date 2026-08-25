"use client";

import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@/config/query-client";
import { fetchAvailability } from "@/lib/api/availability";
import type { AvailabilityParams } from "@/types/availability";

export function useAvailability(params: AvailabilityParams | null) {
  return useQuery({
    queryKey: queryKeys.availability.detail(params),
    queryFn: () => fetchAvailability(params!),
    enabled: Boolean(params?.staff_id && params?.date && params.duration_minutes > 0),
  });
}
