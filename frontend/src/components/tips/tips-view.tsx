"use client";

import { useMemo, useState } from "react";
import { Plus } from "lucide-react";

import { PermissionGate } from "@/components/auth/permission-gate";
import { StaffTipSummaryPanel } from "@/components/tips/staff-tip-summary";
import { TipEditModal } from "@/components/tips/tip-edit-modal";
import { TipFormModal } from "@/components/tips/tip-form-modal";
import { TipsTable } from "@/components/tips/tips-table";
import { ErrorDisplay } from "@/components/feedback/error-display";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAppointments } from "@/hooks/use-appointments";
import { useStaffPerformance, useTeamPerformance } from "@/hooks/use-performance";
import { usePermissions } from "@/hooks/use-permissions";
import { useStaff } from "@/hooks/use-staff";
import { useTipMutations, useTips } from "@/hooks/use-tips";
import { getMonthDateRange } from "@/lib/commissions/summary-utils";
import { toTipCreatePayload, toTipUpdatePayload } from "@/lib/schemas/tip";
import { getCurrentMonthKey, summarizeTips } from "@/lib/tips/summary-utils";
import { toast } from "@/lib/toast";
import type { Appointment } from "@/types/api";
import type { Tip } from "@/types/tips";

function isEligibleForTip(appointment: Appointment) {
  return appointment.status !== "CANCELLED" && appointment.status !== "NO_SHOW";
}

export function TipsView() {
  const { canOne, canAny } = usePermissions();
  const canFilterStaff = canOne("tips:read");
  const canViewTeamPerformance = canOne("performance:read");
  const canViewStaffPerformance = canAny(["performance:read", "performance:read_own"]);

  const [page, setPage] = useState(1);
  const [staffFilter, setStaffFilter] = useState("");
  const [monthKey, setMonthKey] = useState(getCurrentMonthKey);
  const [formOpen, setFormOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [selectedTip, setSelectedTip] = useState<Tip | undefined>();

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

  const tipsQuery = useTips(listParams);
  const summaryTipsQuery = useTips(summaryListParams);
  const appointmentsQuery = useAppointments({ page: 1, limit: 100, sort_by: "appointment_date", sort_order: "desc" });
  const staffQuery = useStaff({ page: 1, limit: 100, sort_by: "name", sort_order: "asc", status: "ACTIVE" });

  const { createTip, updateTip, isCreating, isUpdating } = useTipMutations();

  const eligibleAppointments = useMemo(
    () => (appointmentsQuery.data?.items ?? []).filter(isEligibleForTip),
    [appointmentsQuery.data?.items],
  );

  const listSummary = useMemo(
    () => summarizeTips(summaryTipsQuery.data?.items ?? [], monthKey),
    [summaryTipsQuery.data?.items, monthKey],
  );

  const inferredStaffId = useMemo(() => {
    if (staffFilter) {
      return staffFilter;
    }
    if (!canFilterStaff) {
      return summaryTipsQuery.data?.items[0]?.staff_id;
    }
    return undefined;
  }, [staffFilter, canFilterStaff, summaryTipsQuery.data?.items]);

  const teamPerformanceQuery = useTeamPerformance(
    monthRange,
    canViewTeamPerformance && !inferredStaffId,
  );
  const staffPerformanceQuery = useStaffPerformance(
    inferredStaffId,
    monthRange,
    canViewStaffPerformance && Boolean(inferredStaffId),
  );

  const openEdit = (tip: Tip) => {
    setSelectedTip(tip);
    setEditOpen(true);
  };

  if (tipsQuery.isError) {
    return (
      <ErrorDisplay
        error={tipsQuery.error}
        title="Unable to load tips"
        onRetry={() => tipsQuery.refetch()}
      />
    );
  }

  const totalPages = tipsQuery.data ? Math.ceil(tipsQuery.data.total / tipsQuery.data.limit) : 1;

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
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Tips</h1>
          <p className="text-sm text-muted-foreground">
            Discretionary tips separate from commission, with staff summaries.
          </p>
        </div>
        <PermissionGate permissions={["tips:write"]}>
          <Button type="button" onClick={() => setFormOpen(true)}>
            <Plus className="h-4 w-4" />
            Add tip
          </Button>
        </PermissionGate>
      </div>

      <Card>
        <CardHeader className="space-y-4">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <CardTitle>Staff tip summary</CardTitle>
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
          <StaffTipSummaryPanel
            monthKey={monthKey}
            listSummary={listSummary}
            teamMetrics={!inferredStaffId ? teamPerformanceQuery.data?.items : undefined}
            staffMetric={inferredStaffId ? staffPerformanceQuery.data : undefined}
            loading={performanceLoading || summaryTipsQuery.isLoading}
            error={performanceError}
            onRetry={() => {
              if (inferredStaffId) {
                staffPerformanceQuery.refetch();
              } else {
                teamPerformanceQuery.refetch();
              }
              summaryTipsQuery.refetch();
            }}
            showTeamBreakdown={canViewTeamPerformance && !inferredStaffId}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Tip history</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <TipsTable tips={tipsQuery.data?.items ?? []} loading={tipsQuery.isLoading} onEdit={openEdit} />

          {tipsQuery.data && tipsQuery.data.total > tipsQuery.data.limit ? (
            <div className="flex items-center justify-between border-t border-border pt-4">
              <p className="text-sm text-muted-foreground">
                Page {tipsQuery.data.page} of {totalPages} · {tipsQuery.data.total} tips
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

      <TipFormModal
        open={formOpen}
        appointments={eligibleAppointments}
        loading={isCreating}
        onOpenChange={setFormOpen}
        onSubmit={async (values) => {
          await createTip(toTipCreatePayload(values));
          toast.success("Tip recorded");
        }}
      />

      <TipEditModal
        open={editOpen}
        tip={selectedTip}
        loading={isUpdating}
        onOpenChange={setEditOpen}
        onSubmit={async (values) => {
          if (!selectedTip) {
            return;
          }
          await updateTip({ id: selectedTip.id, payload: toTipUpdatePayload(values) });
          toast.success("Tip updated");
        }}
      />
    </div>
  );
}
