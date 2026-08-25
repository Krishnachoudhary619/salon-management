"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@/config/query-client";
import { fetchAppointmentSeries, fetchRevenueSeries } from "@/lib/api/dashboard";
import { fetchTeamPerformance } from "@/lib/api/performance";
import {
  getReportDateRange,
  normalizeAppointmentReport,
  normalizeRevenueReport,
} from "@/lib/reports/period-utils";
import type { ReportPeriod } from "@/types/reports";

export function useRevenueReport(period: ReportPeriod, enabled = true) {
  const range = useMemo(() => getReportDateRange(period), [period]);
  const params = useMemo(
    () => ({
      ...range,
      group_by: period === "monthly" ? ("month" as const) : ("day" as const),
    }),
    [period, range],
  );

  const query = useQuery({
    queryKey: queryKeys.dashboard.revenue(params),
    queryFn: () => fetchRevenueSeries(params),
    enabled,
  });

  const rows = useMemo(
    () => normalizeRevenueReport(query.data?.items ?? [], period),
    [query.data?.items, period],
  );

  return { ...query, rows, range };
}

export function useAppointmentsReport(period: ReportPeriod, enabled = true) {
  const range = useMemo(() => getReportDateRange(period), [period]);

  const query = useQuery({
    queryKey: queryKeys.dashboard.appointments(range),
    queryFn: () => fetchAppointmentSeries(range),
    enabled,
  });

  const rows = useMemo(
    () => normalizeAppointmentReport(query.data?.items ?? [], period),
    [query.data?.items, period],
  );

  return { ...query, rows, range };
}

export function useStaffPerformanceReport(period: ReportPeriod, enabled = true) {
  const range = useMemo(() => getReportDateRange(period), [period]);

  const query = useQuery({
    queryKey: queryKeys.performance.team(range),
    queryFn: () => fetchTeamPerformance(range),
    enabled,
  });

  return { ...query, rows: query.data?.items ?? [], range };
}
