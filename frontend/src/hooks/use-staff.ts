"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "@/config/query-client";
import {
  createStaff,
  deactivateStaff,
  fetchStaff,
  updateStaff,
} from "@/lib/api/staff";
import type { StaffCreateRequest, StaffListParams, StaffUpdateRequest } from "@/types/staff";

export function useStaff(params: StaffListParams) {
  return useQuery({
    queryKey: queryKeys.staff.list(params),
    queryFn: () => fetchStaff(params),
  });
}

export function useStaffMutations() {
  const queryClient = useQueryClient();

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["staff"] });

  const createMutation = useMutation({
    mutationFn: (payload: StaffCreateRequest) => createStaff(payload),
    onSuccess: invalidate,
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: StaffUpdateRequest }) =>
      updateStaff(id, payload),
    onSuccess: invalidate,
  });

  const deactivateMutation = useMutation({
    mutationFn: (id: string) => deactivateStaff(id),
    onSuccess: invalidate,
  });

  return {
    createStaff: createMutation.mutateAsync,
    updateStaff: updateMutation.mutateAsync,
    deactivateStaff: deactivateMutation.mutateAsync,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeactivating: deactivateMutation.isPending,
  };
}
