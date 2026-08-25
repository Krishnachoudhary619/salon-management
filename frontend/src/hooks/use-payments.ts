"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "@/config/query-client";
import { createPayment, fetchPayments } from "@/lib/api/payments";
import type { PaymentCreateRequest, PaymentListParams } from "@/types/payments";

export function usePayments(params: PaymentListParams) {
  return useQuery({
    queryKey: queryKeys.payments.list(params),
    queryFn: () => fetchPayments(params),
  });
}

export function usePaymentMutations() {
  const queryClient = useQueryClient();

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["payments"] });

  const createMutation = useMutation({
    mutationFn: (payload: PaymentCreateRequest) => createPayment(payload),
    onSuccess: () => {
      invalidate();
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
    },
  });

  return {
    createPayment: createMutation.mutateAsync,
    isCreating: createMutation.isPending,
  };
}
