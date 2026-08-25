"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "@/config/query-client";
import {
  createService,
  deactivateService,
  fetchServices,
  updateService,
} from "@/lib/api/services";
import type { ServiceCreateRequest, ServiceListParams, ServiceUpdateRequest } from "@/types/services";

export function useServices(params: ServiceListParams) {
  return useQuery({
    queryKey: queryKeys.services.list(params),
    queryFn: () => fetchServices(params),
  });
}

export function useServiceMutations() {
  const queryClient = useQueryClient();

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["services"] });

  const createMutation = useMutation({
    mutationFn: (payload: ServiceCreateRequest) => createService(payload),
    onSuccess: invalidate,
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ServiceUpdateRequest }) =>
      updateService(id, payload),
    onSuccess: invalidate,
  });

  const deactivateMutation = useMutation({
    mutationFn: (id: string) => deactivateService(id),
    onSuccess: invalidate,
  });

  return {
    createService: createMutation.mutateAsync,
    updateService: updateMutation.mutateAsync,
    deactivateService: deactivateMutation.mutateAsync,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeactivating: deactivateMutation.isPending,
  };
}
