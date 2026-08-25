"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "@/config/query-client";
import { createTip, fetchTip, fetchTips, updateTip } from "@/lib/api/tips";
import type { TipCreateRequest, TipListParams, TipUpdateRequest } from "@/types/tips";

export function useTips(params: TipListParams) {
  return useQuery({
    queryKey: queryKeys.tips.list(params),
    queryFn: () => fetchTips(params),
  });
}

export function useTip(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.tips.detail(id ?? ""),
    queryFn: () => fetchTip(id!),
    enabled: Boolean(id),
  });
}

export function useTipMutations() {
  const queryClient = useQueryClient();

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["tips"] });

  const createMutation = useMutation({
    mutationFn: (payload: TipCreateRequest) => createTip(payload),
    onSuccess: invalidate,
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: TipUpdateRequest }) =>
      updateTip(id, payload),
    onSuccess: invalidate,
  });

  return {
    createTip: createMutation.mutateAsync,
    updateTip: updateMutation.mutateAsync,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
  };
}
