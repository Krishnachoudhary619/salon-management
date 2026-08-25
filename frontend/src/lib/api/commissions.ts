import { apiClient, apiRequest } from "@/lib/api/client";
import { apiEndpoints } from "@/config/routes";
import type { PaginatedData } from "@/types/api";
import type { Commission, CommissionListParams } from "@/types/commissions";

export async function fetchCommissions(
  params: CommissionListParams = {},
): Promise<PaginatedData<Commission>> {
  return apiRequest(() => apiClient.get(apiEndpoints.commissions.list, { params }));
}

export async function fetchStaffCommissions(
  staffId: string,
  params: Omit<CommissionListParams, "staff_id"> = {},
): Promise<PaginatedData<Commission>> {
  return apiRequest(() => apiClient.get(apiEndpoints.commissions.byStaff(staffId), { params }));
}

export async function fetchCommission(id: string): Promise<Commission> {
  return apiRequest(() => apiClient.get(apiEndpoints.commissions.detail(id)));
}
