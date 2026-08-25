import { apiClient, apiRequest, apiRequestOptional } from "@/lib/api/client";
import { apiEndpoints } from "@/config/routes";
import type { PaginatedData } from "@/types/api";
import type {
  Service,
  ServiceCreateRequest,
  ServiceListParams,
  ServiceUpdateRequest,
} from "@/types/services";

export async function fetchServices(params: ServiceListParams = {}): Promise<PaginatedData<Service>> {
  return apiRequest(() => apiClient.get(apiEndpoints.services.list, { params }));
}

export async function createService(payload: ServiceCreateRequest): Promise<Service> {
  return apiRequest(() => apiClient.post(apiEndpoints.services.list, payload));
}

export async function updateService(id: string, payload: ServiceUpdateRequest): Promise<Service> {
  return apiRequest(() => apiClient.put(apiEndpoints.services.detail(id), payload));
}

export async function deactivateService(id: string): Promise<void> {
  await apiRequestOptional(() => apiClient.delete(apiEndpoints.services.detail(id)));
}
