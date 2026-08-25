"use client";

import { CalendarDays, IndianRupee, TrendingUp, Users } from "lucide-react";

import { AppointmentTrendChart } from "@/components/dashboard/appointment-trend-chart";
import { RevenueTrendChart } from "@/components/dashboard/revenue-trend-chart";
import { StatCard } from "@/components/dashboard/stat-card";
import { TopStaffTable } from "@/components/dashboard/top-staff-table";
import { UpcomingAppointmentsTable } from "@/components/dashboard/upcoming-appointments-table";
import { ErrorDisplay } from "@/components/feedback/error-display";
import {
  useAppointmentTrend,
  useDashboardOverview,
  useRevenueTrend,
  useTopStaff,
  useUpcomingAppointments,
} from "@/hooks/use-dashboard";
import { formatCurrency, formatDateTimeLabel } from "@/lib/format";

export function DashboardView() {
  const overviewQuery = useDashboardOverview();
  const revenueQuery = useRevenueTrend();
  const appointmentTrendQuery = useAppointmentTrend();
  const upcomingQuery = useUpcomingAppointments();
  const topStaffQuery = useTopStaff();

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
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          {overview?.as_of
            ? `Overview as of ${formatDateTimeLabel(overview.as_of)}`
            : "Salon performance overview"}
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Today's Revenue"
          value={formatCurrency(overview?.revenue_today ?? "0")}
          icon={IndianRupee}
          loading={overviewLoading}
        />
        <StatCard
          title="Monthly Revenue"
          value={formatCurrency(overview?.revenue_this_month ?? "0")}
          icon={TrendingUp}
          loading={overviewLoading}
        />
        <StatCard
          title="Today's Appointments"
          value={String(overview?.appointments_today ?? 0)}
          icon={CalendarDays}
          loading={overviewLoading}
        />
        <StatCard
          title="Customers Served"
          value={String(overview?.customers_served ?? 0)}
          description="Completed visits today"
          icon={Users}
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
        />
        <TopStaffTable staff={topStaffQuery.data?.items ?? []} loading={topStaffQuery.isLoading} />
      </div>
    </div>
  );
}
