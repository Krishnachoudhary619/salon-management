import { apiClient, apiRequest } from "@/lib/api/client";
import { apiEndpoints } from "@/config/routes";
import type {
  PerformanceDateRangeParams,
  StaffPerformanceResponse,
  TeamPerformanceResponse,
} from "@/types/performance";

export async function fetchTeamPerformance(
  params: PerformanceDateRangeParams = {},
): Promise<TeamPerformanceResponse> {
  return apiRequest(() => apiClient.get(apiEndpoints.performance.team, { params }));
}

export async function fetchStaffPerformance(
  staffId: string,
  params: PerformanceDateRangeParams = {},
): Promise<StaffPerformanceResponse> {
  return apiRequest(() => apiClient.get(apiEndpoints.performance.staff(staffId), { params }));
}
