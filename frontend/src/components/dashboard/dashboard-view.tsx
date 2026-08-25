"use client";

import { useState } from "react";
import { CalendarDays, IndianRupee, Sparkles, TrendingUp, Users } from "lucide-react";

import { formatDashboardDate, getFirstName, getGreeting } from "@/components/dashboard/dashboard-utils";
import { useAuth } from "@/hooks/use-auth";

import { CompleteAppointmentDialog } from "@/components/appointments/complete-appointment-dialog";
import { ConfirmAppointmentDialog } from "@/components/appointments/confirm-appointment-dialog";
import { PaymentFormModal } from "@/components/payments/payment-form-modal";
import { AppointmentTrendChart } from "@/components/dashboard/appointment-trend-chart";
import { RevenueTrendChart } from "@/components/dashboard/revenue-trend-chart";
import { StatCard } from "@/components/dashboard/stat-card";
import { TopStaffTable } from "@/components/dashboard/top-staff-table";
import { UpcomingAppointmentsTable } from "@/components/dashboard/upcoming-appointments-table";
import { ErrorDisplay } from "@/components/feedback/error-display";
import { useAppointmentMutations } from "@/hooks/use-appointments";
import { usePaymentMutations } from "@/hooks/use-payments";
import { usePermissions } from "@/hooks/use-permissions";
import {
  useAppointmentTrend,
  useDashboardOverview,
  useRevenueTrend,
  useTopStaff,
  useUpcomingAppointments,
} from "@/hooks/use-dashboard";
import { useStaff } from "@/hooks/use-staff";
import { getVisitActionLabel } from "@/lib/appointments/status-colors";
import { formatCurrency, formatDateTimeLabel } from "@/lib/format";
import { toPaymentCreatePayload } from "@/lib/schemas/payment";
import { toast } from "@/lib/toast";
import type { Appointment } from "@/types/api";

export function DashboardView() {
  const overviewQuery = useDashboardOverview();
  const revenueQuery = useRevenueTrend();
  const appointmentTrendQuery = useAppointmentTrend();
  const upcomingQuery = useUpcomingAppointments();
  const topStaffQuery = useTopStaff();
  const staffQuery = useStaff({ page: 1, limit: 100, sort_by: "name", sort_order: "asc", status: "ACTIVE" });
  const { changeAppointmentStatus, isChangingStatus } = useAppointmentMutations();
  const { createPayment, isCreating: isRecordingPayment } = usePaymentMutations();
  const { user } = useAuth();
  const { canAny } = usePermissions();
  const canRecordPayment = canAny(["payments:write"]);
  const [confirming, setConfirming] = useState<Appointment | undefined>();
  const [completing, setCompleting] = useState<Appointment | undefined>();
  const [paying, setPaying] = useState<Appointment | undefined>();

  const overviewLoading = overviewQuery.isLoading;
  const overview = overviewQuery.data;

  if (overviewQuery.isError) {
    return (
      <ErrorDisplay
        error={overviewQuery.error}
        title="Unable to load dashboard"
        onRetry={() => overviewQuery.refetch()}
      />
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground">{formatDashboardDate()}</p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight">
            {getGreeting()}, {getFirstName(user?.name)}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {overview?.as_of
              ? `Updated ${formatDateTimeLabel(overview.as_of)}`
              : "Today’s book and takings"}
          </p>
        </div>
        <div className="inline-flex items-center gap-2 self-start rounded-full border border-border/70 bg-card px-3 py-1.5 text-sm text-muted-foreground">
          <Sparkles className="h-4 w-4 text-amber-500" />
          Avg ticket {formatCurrency(overview?.average_ticket_size ?? "0")}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Today’s revenue"
          value={formatCurrency(overview?.revenue_today ?? "0")}
          icon={IndianRupee}
          tone="emerald"
          loading={overviewLoading}
        />
        <StatCard
          title="This month"
          value={formatCurrency(overview?.revenue_this_month ?? "0")}
          icon={TrendingUp}
          tone="blue"
          loading={overviewLoading}
        />
        <StatCard
          title="Appointments today"
          value={String(overview?.appointments_today ?? 0)}
          icon={CalendarDays}
          tone="amber"
          loading={overviewLoading}
        />
        <StatCard
          title="Customers served"
          value={String(overview?.customers_served ?? 0)}
          description="Completed visits today"
          icon={Users}
          tone="violet"
          loading={overviewLoading}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <RevenueTrendChart
          items={revenueQuery.data?.items ?? []}
          loading={revenueQuery.isLoading}
        />
        <AppointmentTrendChart
          items={appointmentTrendQuery.data?.items ?? []}
          loading={appointmentTrendQuery.isLoading}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <UpcomingAppointmentsTable
          appointments={upcomingQuery.data ?? []}
          loading={upcomingQuery.isLoading}
          onConfirm={setConfirming}
          onComplete={setCompleting}
          onAdvance={async (appointment, status) => {
            try {
              await changeAppointmentStatus({
                id: appointment.id,
                payload: { status },
              });
              toast.success(getVisitActionLabel(appointment.status) ?? "Appointment updated");
            } catch (error) {
              toast.fromError(error, "Unable to update appointment");
            }
          }}
        />
        <TopStaffTable staff={topStaffQuery.data?.items ?? []} loading={topStaffQuery.isLoading} />
      </div>

      <CompleteAppointmentDialog
        open={Boolean(completing)}
        appointment={completing}
        loading={isChangingStatus}
        onOpenChange={(open) => {
          if (!open) {
            setCompleting(undefined);
          }
        }}
        onConfirm={async () => {
          if (!completing) {
            return;
          }
          try {
            const updated = await changeAppointmentStatus({
              id: completing.id,
              payload: { status: "COMPLETED" },
            });
            toast.success("Visit completed. Invoice created.");
            if (canRecordPayment) {
              setPaying(updated);
            }
          } catch (error) {
            toast.fromError(error, "Unable to complete appointment");
            throw error;
          }
        }}
      />

      <PaymentFormModal
        open={Boolean(paying)}
        appointments={paying ? [paying] : []}
        defaultAppointmentId={paying?.id}
        loading={isRecordingPayment}
        onOpenChange={(open) => {
          if (!open) {
            setPaying(undefined);
          }
        }}
        onSubmit={async (values) => {
          await createPayment(toPaymentCreatePayload(values));
          toast.success("Payment recorded");
        }}
      />

      <ConfirmAppointmentDialog
        open={Boolean(confirming)}
        appointment={confirming}
        staff={staffQuery.data?.items ?? []}
        loading={isChangingStatus}
        onOpenChange={(open) => {
          if (!open) {
            setConfirming(undefined);
          }
        }}
        onConfirm={async (staffId) => {
          if (!confirming) {
            return;
          }
          try {
            await changeAppointmentStatus({
              id: confirming.id,
              payload: { status: "CONFIRMED", staff_id: staffId },
            });
            toast.success("Appointment confirmed");
          } catch (error) {
            toast.fromError(error, "Unable to confirm appointment");
            throw error;
          }
        }}
      />
    </div>
  );
}
