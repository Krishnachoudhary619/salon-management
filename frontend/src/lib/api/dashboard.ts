import { apiClient, apiRequest } from "@/lib/api/client";
import { apiEndpoints } from "@/config/routes";
import type {
  AppointmentSeries,
  DashboardOverview,
  DashboardRevenueParams,
  DashboardDateRangeParams,
  RevenueSeries,
  TopPerformers,
  TopPerformersParams,
} from "@/types/dashboard";

export async function fetchDashboardOverview(): Promise<DashboardOverview> {
  return apiRequest(() => apiClient.get(apiEndpoints.dashboard.overview));
}

export async function fetchRevenueSeries(params: DashboardRevenueParams = {}): Promise<RevenueSeries> {
  return apiRequest(() => apiClient.get(apiEndpoints.dashboard.revenue, { params }));
}

export async function fetchAppointmentSeries(
  params: DashboardDateRangeParams = {},
): Promise<AppointmentSeries> {
  return apiRequest(() => apiClient.get(apiEndpoints.dashboard.appointments, { params }));
}

export async function fetchTopPerformers(params: TopPerformersParams = {}): Promise<TopPerformers> {
  return apiRequest(() => apiClient.get(apiEndpoints.dashboard.topPerformers, { params }));
}
