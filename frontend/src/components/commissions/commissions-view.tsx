"use client";

import { useMemo, useState } from "react";

import { CommissionDetailModal } from "@/components/commissions/commission-detail-modal";
import { CommissionsTable } from "@/components/commissions/commissions-table";
import { MonthlySummary } from "@/components/commissions/monthly-summary";
import { ErrorDisplay } from "@/components/feedback/error-display";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCommissions } from "@/hooks/use-commissions";
import { useStaffPerformance, useTeamPerformance } from "@/hooks/use-performance";
import { usePermissions } from "@/hooks/use-permissions";
import { useStaff } from "@/hooks/use-staff";
import {
  getCurrentMonthKey,
  getMonthDateRange,
  summarizeCommissions,
} from "@/lib/commissions/summary-utils";
import type { Commission } from "@/types/commissions";

export function CommissionsView() {
  const { canOne, canAny } = usePermissions();
  const canFilterStaff = canOne("commissions:read");
  const canViewTeamPerformance = canOne("performance:read");
  const canViewStaffPerformance = canAny(["performance:read", "performance:read_own"]);

  const [page, setPage] = useState(1);
  const [staffFilter, setStaffFilter] = useState("");
  const [monthKey, setMonthKey] = useState(getCurrentMonthKey);
  const [selectedCommission, setSelectedCommission] = useState<Commission | undefined>();
  const [detailOpen, setDetailOpen] = useState(false);

  const monthRange = useMemo(() => getMonthDateRange(monthKey), [monthKey]);

  const listParams = useMemo(
    () => ({
      page,
      limit: 10,
      sort_by: "created_at",
      sort_order: "desc" as const,
      staff_id: staffFilter || undefined,
    }),
    [page, staffFilter],
  );

  const summaryListParams = useMemo(
    () => ({
      page: 1,
      limit: 100,
      sort_by: "created_at",
      sort_order: "desc" as const,
      staff_id: staffFilter || undefined,
    }),
    [staffFilter],
  );

  const commissionsQuery = useCommissions(listParams);
  const summaryCommissionsQuery = useCommissions(summaryListParams);
  const staffQuery = useStaff({ page: 1, limit: 100, sort_by: "name", sort_order: "asc", status: "ACTIVE" });

  const inferredStaffId = useMemo(() => {
    if (staffFilter) {
      return staffFilter;
    }
    if (!canFilterStaff) {
      return summaryCommissionsQuery.data?.items[0]?.staff_id;
    }
    return undefined;
  }, [staffFilter, canFilterStaff, summaryCommissionsQuery.data?.items]);

  const teamPerformanceQuery = useTeamPerformance(
    monthRange,
    canViewTeamPerformance && !inferredStaffId,
  );
  const staffPerformanceQuery = useStaffPerformance(
    inferredStaffId,
    monthRange,
    canViewStaffPerformance && Boolean(inferredStaffId),
  );

  const listSummary = useMemo(
    () => summarizeCommissions(summaryCommissionsQuery.data?.items ?? [], monthKey),
    [summaryCommissionsQuery.data?.items, monthKey],
  );

  const openDetail = (commission: Commission) => {
    setSelectedCommission(commission);
    setDetailOpen(true);
  };

  if (commissionsQuery.isError) {
    return (
      <ErrorDisplay
        error={commissionsQuery.error}
        title="Unable to load commissions"
        onRetry={() => commissionsQuery.refetch()}
      />
    );
  }

  const totalPages = commissionsQuery.data
    ? Math.ceil(commissionsQuery.data.total / commissionsQuery.data.limit)
    : 1;

  const performanceLoading =
    (canViewTeamPerformance && !inferredStaffId && teamPerformanceQuery.isLoading) ||
    (canViewStaffPerformance && inferredStaffId && staffPerformanceQuery.isLoading);

  const performanceError =
    canViewTeamPerformance && !inferredStaffId
      ? teamPerformanceQuery.error
      : canViewStaffPerformance && inferredStaffId
        ? staffPerformanceQuery.error
        : undefined;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Commissions</h1>
        <p className="text-sm text-muted-foreground">
          Historical commission snapshots with monthly summaries and staff filtering.
        </p>
      </div>

      <Card>
        <CardHeader className="space-y-4">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <CardTitle>Monthly summary</CardTitle>
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
                  onChange={(event) => {
                    setStaffFilter(event.target.value);
                    setPage(1);
                  }}
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm lg:min-w-56"
                >
                  <option value="">All staff</option>
                  {(staffQuery.data?.items ?? []).map((member) => (
                    <option key={member.id} value={member.id}>
                      {member.name}
                    </option>
                  ))}
                </select>
              ) : null}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <MonthlySummary
            monthKey={monthKey}
            listSummary={listSummary}
            teamMetrics={!inferredStaffId ? teamPerformanceQuery.data?.items : undefined}
            staffMetric={inferredStaffId ? staffPerformanceQuery.data : undefined}
            loading={performanceLoading || summaryCommissionsQuery.isLoading}
            error={performanceError}
            onRetry={() => {
              if (inferredStaffId) {
                staffPerformanceQuery.refetch();
              } else {
                teamPerformanceQuery.refetch();
              }
              summaryCommissionsQuery.refetch();
            }}
            showTeamBreakdown={canViewTeamPerformance && !inferredStaffId}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Commission history</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <CommissionsTable
            commissions={commissionsQuery.data?.items ?? []}
            loading={commissionsQuery.isLoading}
            onView={openDetail}
          />

          {commissionsQuery.data && commissionsQuery.data.total > commissionsQuery.data.limit ? (
            <div className="flex items-center justify-between border-t border-border pt-4">
              <p className="text-sm text-muted-foreground">
                Page {commissionsQuery.data.page} of {totalPages} · {commissionsQuery.data.total}{" "}
                commissions
              </p>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((current) => current - 1)}
                >
                  Previous
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((current) => current + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <CommissionDetailModal
        open={detailOpen}
        commissionId={selectedCommission?.id}
        fallback={selectedCommission}
        onOpenChange={setDetailOpen}
      />
    </div>
  );
}
