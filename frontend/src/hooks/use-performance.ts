"use client";

import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@/config/query-client";
import { fetchStaffPerformance, fetchTeamPerformance } from "@/lib/api/performance";
import type { PerformanceDateRangeParams } from "@/types/performance";

export function useTeamPerformance(params: PerformanceDateRangeParams, enabled = true) {
  return useQuery({
    queryKey: queryKeys.performance.team(params),
    queryFn: () => fetchTeamPerformance(params),
    enabled,
  });
}

export function useStaffPerformance(
  staffId: string | undefined,
  params: PerformanceDateRangeParams,
  enabled = true,
) {
  return useQuery({
    queryKey: queryKeys.performance.staff(staffId ?? "", params),
    queryFn: () => fetchStaffPerformance(staffId!, params),
    enabled: enabled && Boolean(staffId),
  });
}
