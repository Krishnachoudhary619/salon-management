import { formatChartDayLabel, formatChartMonthLabel, getDateRange, getMonthRange, toIsoDate } from "@/lib/format";
import type { AppointmentDayPoint, RevenuePoint } from "@/types/dashboard";
import type { AppointmentReportRow, ReportDateRange, ReportPeriod, RevenueReportRow } from "@/types/reports";

export const REPORT_PERIOD_LABELS: Record<ReportPeriod, string> = {
  daily: "Daily",
  weekly: "Weekly",
  monthly: "Monthly",
};

export const REPORT_TYPE_LABELS = {
  revenue: "Revenue",
  appointments: "Appointments",
  staff_performance: "Staff Performance",
} as const;

export function getReportDateRange(period: ReportPeriod): ReportDateRange {
  switch (period) {
    case "daily":
      return getDateRange(30);
    case "weekly":
      return getDateRange(84);
    case "monthly":
      return getMonthRange(12);
  }
}

export function getReportPeriodDescription(period: ReportPeriod): string {
  switch (period) {
    case "daily":
      return "Last 30 days";
    case "weekly":
      return "Last 12 weeks";
    case "monthly":
      return "Last 12 months";
  }
}

function parseLocalDate(value: string) {
  return new Date(`${value}T00:00:00`);
}

function getWeekStartKey(value: string) {
  const date = parseLocalDate(value);
  const day = date.getDay();
  const diff = date.getDate() - day + (day === 0 ? -6 : 1);
  date.setDate(diff);
  return toIsoDate(date);
}

function formatWeekLabel(weekStart: string) {
  return `Week of ${formatChartDayLabel(weekStart)}`;
}

export function normalizeRevenueReport(
  items: RevenuePoint[],
  period: ReportPeriod,
): RevenueReportRow[] {
  if (period === "daily") {
    return items.map((item) => ({
      period: item.period,
      label: formatChartDayLabel(item.period),
      revenue: Number.parseFloat(item.revenue),
    }));
  }

  if (period === "weekly") {
    const buckets = new Map<string, number>();
    for (const item of items) {
      const weekKey = getWeekStartKey(item.period);
      buckets.set(weekKey, (buckets.get(weekKey) ?? 0) + Number.parseFloat(item.revenue));
    }
    return [...buckets.entries()]
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([weekStart, revenue]) => ({
        period: weekStart,
        label: formatWeekLabel(weekStart),
        revenue,
      }));
  }

  return items.map((item) => ({
    period: item.period,
    label: formatChartMonthLabel(item.period),
    revenue: Number.parseFloat(item.revenue),
  }));
}

export function normalizeAppointmentReport(
  items: AppointmentDayPoint[],
  period: ReportPeriod,
): AppointmentReportRow[] {
  if (period === "daily") {
    return items.map((item) => ({
      period: item.appointment_date,
      label: formatChartDayLabel(item.appointment_date),
      total: item.total,
      completed: item.completed,
      cancelled: item.cancelled,
    }));
  }

  const buckets = new Map<
    string,
    { total: number; completed: number; cancelled: number; label: string }
  >();

  for (const item of items) {
    const key = period === "weekly" ? getWeekStartKey(item.appointment_date) : item.appointment_date.slice(0, 7);
    const label =
      period === "weekly" ? formatWeekLabel(key) : formatChartMonthLabel(key);
    const current = buckets.get(key) ?? { total: 0, completed: 0, cancelled: 0, label };
    buckets.set(key, {
      label,
      total: current.total + item.total,
      completed: current.completed + item.completed,
      cancelled: current.cancelled + item.cancelled,
    });
  }

  return [...buckets.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([bucketKey, values]) => ({
      period: bucketKey,
      label: values.label,
      total: values.total,
      completed: values.completed,
      cancelled: values.cancelled,
    }));
}

export function sumRevenue(rows: RevenueReportRow[]) {
  return rows.reduce((sum, row) => sum + row.revenue, 0);
}

export function sumAppointments(rows: AppointmentReportRow[]) {
  return rows.reduce(
    (acc, row) => ({
      total: acc.total + row.total,
      completed: acc.completed + row.completed,
      cancelled: acc.cancelled + row.cancelled,
    }),
    { total: 0, completed: 0, cancelled: 0 },
  );
}
