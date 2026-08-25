import { apiClient, apiRequest } from "@/lib/api/client";
import { apiEndpoints } from "@/config/routes";
import type { PaginatedData } from "@/types/api";
import type {
  Payment,
  PaymentCreateRequest,
  PaymentListParams,
} from "@/types/payments";

export async function fetchPayments(params: PaymentListParams = {}): Promise<PaginatedData<Payment>> {
  return apiRequest(() => apiClient.get(apiEndpoints.payments.list, { params }));
}

export async function createPayment(payload: PaymentCreateRequest): Promise<Payment> {
  return apiRequest(() => apiClient.post(apiEndpoints.payments.list, payload));
}
