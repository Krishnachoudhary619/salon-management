import { apiClient, apiRequest } from "@/lib/api/client";
import { apiEndpoints } from "@/config/routes";
import type { PaginatedData } from "@/types/api";
import type { Tip, TipCreateRequest, TipListParams, TipUpdateRequest } from "@/types/tips";

export async function fetchTips(params: TipListParams = {}): Promise<PaginatedData<Tip>> {
  return apiRequest(() => apiClient.get(apiEndpoints.tips.list, { params }));
}

export async function fetchStaffTips(
  staffId: string,
  params: Omit<TipListParams, "staff_id"> = {},
): Promise<PaginatedData<Tip>> {
  return apiRequest(() => apiClient.get(apiEndpoints.tips.byStaff(staffId), { params }));
}

export async function fetchTip(id: string): Promise<Tip> {
  return apiRequest(() => apiClient.get(apiEndpoints.tips.detail(id)));
}

export async function createTip(payload: TipCreateRequest): Promise<Tip> {
  return apiRequest(() => apiClient.post(apiEndpoints.tips.list, payload));
}

export async function updateTip(id: string, payload: TipUpdateRequest): Promise<Tip> {
  return apiRequest(() => apiClient.put(apiEndpoints.tips.detail(id), payload));
}
