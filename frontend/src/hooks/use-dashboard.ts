"use client";

import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@/config/query-client";
import { fetchUpcomingAppointments } from "@/lib/api/appointments";
import {
  fetchAppointmentSeries,
  fetchDashboardOverview,
  fetchRevenueSeries,
  fetchTopPerformers,
} from "@/lib/api/dashboard";
import { getDateRange, getMonthRange } from "@/lib/format";
import type { DashboardDateRangeParams, TopPerformersParams } from "@/types/dashboard";

const REVENUE_TREND_RANGE = getDateRange(30);
const APPOINTMENT_TREND_RANGE = getDateRange(30);
const TOP_STAFF_RANGE = getMonthRange(1);

export function useDashboardOverview() {
  return useQuery({
    queryKey: queryKeys.dashboard.overview,
    queryFn: fetchDashboardOverview,
  });
}

export function useRevenueTrend() {
  const params = {
    ...REVENUE_TREND_RANGE,
    group_by: "day" as const,
  };

  return useQuery({
    queryKey: queryKeys.dashboard.revenue(params),
    queryFn: () => fetchRevenueSeries(params),
  });
}

export function useAppointmentTrend() {
  const params: DashboardDateRangeParams = APPOINTMENT_TREND_RANGE;

  return useQuery({
    queryKey: queryKeys.dashboard.appointments(params),
    queryFn: () => fetchAppointmentSeries(params),
  });
}

export function useTopStaff() {
  const params: TopPerformersParams = {
    ...TOP_STAFF_RANGE,
    limit: 5,
  };

  return useQuery({
    queryKey: queryKeys.dashboard.topPerformers(params),
    queryFn: () => fetchTopPerformers(params),
  });
}

export function useUpcomingAppointments(limit = 8) {
  return useQuery({
    queryKey: queryKeys.dashboard.upcomingAppointments(limit),
    queryFn: () => fetchUpcomingAppointments({ limit }),
  });
}
