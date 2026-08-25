"use client";

import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@/config/query-client";
import { fetchCommission, fetchCommissions, fetchStaffCommissions } from "@/lib/api/commissions";
import type { CommissionListParams } from "@/types/commissions";

export function useCommissions(params: CommissionListParams, enabled = true) {
  return useQuery({
    queryKey: queryKeys.commissions.list(params),
    queryFn: () => fetchCommissions(params),
    enabled,
  });
}

export function useStaffCommissions(staffId: string | undefined, params: Omit<CommissionListParams, "staff_id">) {
  return useQuery({
    queryKey: queryKeys.commissions.byStaff(staffId ?? "", params),
    queryFn: () => fetchStaffCommissions(staffId!, params),
    enabled: Boolean(staffId),
  });
}

export function useCommission(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.commissions.detail(id ?? ""),
    queryFn: () => fetchCommission(id!),
    enabled: Boolean(id),
  });
}
