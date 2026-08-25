import { apiClient, apiRequest, apiRequestOptional } from "@/lib/api/client";
import { apiEndpoints } from "@/config/routes";
import type { PaginatedData } from "@/types/api";
import type {
  StaffCreateRequest,
  StaffListParams,
  StaffMember,
  StaffUpdateRequest,
} from "@/types/staff";

export async function fetchStaff(params: StaffListParams = {}): Promise<PaginatedData<StaffMember>> {
  return apiRequest(() => apiClient.get(apiEndpoints.staff.list, { params }));
}

export async function fetchStaffMember(id: string): Promise<StaffMember> {
  return apiRequest(() => apiClient.get(apiEndpoints.staff.detail(id)));
}

export async function createStaff(payload: StaffCreateRequest): Promise<StaffMember> {
  return apiRequest(() => apiClient.post(apiEndpoints.staff.list, payload));
}

export async function updateStaff(id: string, payload: StaffUpdateRequest): Promise<StaffMember> {
  return apiRequest(() => apiClient.put(apiEndpoints.staff.detail(id), payload));
}

export async function deactivateStaff(id: string): Promise<void> {
  await apiRequestOptional(() => apiClient.delete(apiEndpoints.staff.detail(id)));
}
