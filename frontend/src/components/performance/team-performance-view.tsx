"use client";

import { useMemo, useState } from "react";

import { PerformanceAppointmentsChart } from "@/components/performance/performance-appointments-chart";
import { PerformanceEarningsChart } from "@/components/performance/performance-earnings-chart";
import { PerformanceSummaryCards } from "@/components/performance/performance-summary-cards";
import { PerformanceTable } from "@/components/performance/performance-table";
import { ErrorDisplay } from "@/components/feedback/error-display";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCommissions } from "@/hooks/use-commissions";
import { useStaffPerformance, useTeamPerformance } from "@/hooks/use-performance";
import { usePermissions } from "@/hooks/use-permissions";
import { useStaff } from "@/hooks/use-staff";
import {
  formatMonthLabel,
  getCurrentMonthKey,
  getMonthDateRange,
} from "@/lib/commissions/summary-utils";
import {
  staffMetricToRows,
  summarizePerformance,
  toAppointmentsChartData,
  toEarningsChartData,
} from "@/lib/performance/summary-utils";

export function TeamPerformanceView() {
  const { canOne, canAny } = usePermissions();
  const canFilterStaff = canOne("performance:read");
  const canViewTeam = canOne("performance:read");
  const canViewStaff = canAny(["performance:read", "performance:read_own"]);

  const [monthKey, setMonthKey] = useState(getCurrentMonthKey);
  const [staffFilter, setStaffFilter] = useState("");

  const monthRange = useMemo(() => getMonthDateRange(monthKey), [monthKey]);

  const staffListQuery = useStaff({
    page: 1,
    limit: 100,
    sort_by: "name",
    sort_order: "asc",
    status: "ACTIVE",
  });

  const ownStaffProbeQuery = useCommissions(
    { page: 1, limit: 1, sort_by: "created_at", sort_order: "desc" },
    !canFilterStaff && canViewStaff,
  );

  const inferredStaffId = useMemo(() => {
    if (staffFilter) {
      return staffFilter;
    }
    if (!canFilterStaff) {
      return ownStaffProbeQuery.data?.items[0]?.staff_id;
    }
    return undefined;
  }, [staffFilter, canFilterStaff, ownStaffProbeQuery.data?.items]);

  const teamQuery = useTeamPerformance(monthRange, canViewTeam && !inferredStaffId);
  const staffPerformanceQuery = useStaffPerformance(
    inferredStaffId,
    monthRange,
    canViewStaff && Boolean(inferredStaffId),
  );

  const activeQuery = inferredStaffId ? staffPerformanceQuery : teamQuery;

  const rows = useMemo(() => {
    if (inferredStaffId && staffPerformanceQuery.data) {
      return staffMetricToRows(staffPerformanceQuery.data);
    }
    return teamQuery.data?.items ?? [];
  }, [inferredStaffId, staffPerformanceQuery.data, teamQuery.data?.items]);

  const totals = useMemo(() => summarizePerformance(rows), [rows]);
  const earningsChartData = useMemo(() => toEarningsChartData(rows), [rows]);
  const appointmentsChartData = useMemo(() => toAppointmentsChartData(rows), [rows]);

  const isTeamView = canViewTeam && !inferredStaffId;
  const pageTitle = isTeamView ? "Team Performance" : "My Performance";
  const pageDescription = isTeamView
    ? "Revenue, appointments, commission, and tips across the salon team."
    : "Your revenue, appointments, commission, and tips for the selected period.";

  if (activeQuery.isError) {
    return (
      <ErrorDisplay
        error={activeQuery.error}
        title="Unable to load performance data"
        onRetry={() => activeQuery.refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{pageTitle}</h1>
        <p className="text-sm text-muted-foreground">{pageDescription}</p>
      </div>

      <Card>
        <CardHeader className="space-y-4">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <CardTitle>{formatMonthLabel(monthKey)}</CardTitle>
              <p className="mt-1 text-sm text-muted-foreground">
                {monthRange.start_date} to {monthRange.end_date}
              </p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <input
                type="month"
                value={monthKey}
                onChange={(event) => setMonthKey(event.target.value)}
                className="h-10 rounded-md border border-input bg-background px-3 text-sm"
              />
              {canFilterStaff ? (
                <select
                  value={staffFilter}
                  onChange={(event) => setStaffFilter(event.target.value)}
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm lg:min-w-56"
                >
                  <option value="">All staff</option>
                  {(staffListQuery.data?.items ?? []).map((member) => (
                    <option key={member.id} value={member.id}>
                      {member.name}
                    </option>
                  ))}
                </select>
              ) : null}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <PerformanceSummaryCards totals={totals} loading={activeQuery.isLoading} />

          <div className="grid gap-4 lg:grid-cols-2">
            <PerformanceEarningsChart data={earningsChartData} loading={activeQuery.isLoading} />
            <PerformanceAppointmentsChart
              data={appointmentsChartData}
              loading={activeQuery.isLoading}
            />
          </div>

          <PerformanceTable
            rows={rows}
            loading={activeQuery.isLoading}
            showStaffColumn={isTeamView}
          />
        </CardContent>
      </Card>
    </div>
  );
}
