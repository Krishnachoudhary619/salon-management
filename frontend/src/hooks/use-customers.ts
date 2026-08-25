"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "@/config/query-client";
import { createCustomer, fetchCustomer, fetchCustomers } from "@/lib/api/customers";
import type { CustomerCreateRequest, CustomerListParams } from "@/types/customers";

export function useCustomers(params: CustomerListParams) {
  return useQuery({
    queryKey: queryKeys.customers.list(params),
    queryFn: () => fetchCustomers(params),
  });
}

export function useCustomer(id: string) {
  return useQuery({
    queryKey: queryKeys.customers.detail(id),
    queryFn: () => fetchCustomer(id),
    enabled: Boolean(id),
  });
}

export function useCustomerMutations() {
  const queryClient = useQueryClient();

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["customers"] });

  const createMutation = useMutation({
    mutationFn: (payload: CustomerCreateRequest) => createCustomer(payload),
    onSuccess: invalidate,
  });

  return {
    createCustomer: createMutation.mutateAsync,
    isCreating: createMutation.isPending,
  };
}
