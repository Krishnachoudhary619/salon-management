import { apiClient, apiRequest } from "@/lib/api/client";
import { apiEndpoints } from "@/config/routes";
import type { PaginatedData } from "@/types/api";
import type { Customer, CustomerCreateRequest, CustomerListParams } from "@/types/customers";

export async function fetchCustomers(params: CustomerListParams = {}): Promise<PaginatedData<Customer>> {
  return apiRequest(() => apiClient.get(apiEndpoints.customers.list, { params }));
}

export async function fetchCustomer(id: string): Promise<Customer> {
  return apiRequest(() => apiClient.get(apiEndpoints.customers.detail(id)));
}

export async function createCustomer(payload: CustomerCreateRequest): Promise<Customer> {
  return apiRequest(() => apiClient.post(apiEndpoints.customers.list, payload));
}
