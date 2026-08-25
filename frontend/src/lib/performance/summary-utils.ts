import type { StaffPerformanceMetrics } from "@/types/performance";

export interface PerformanceTotals {
  revenue: number;
  appointments: number;
  commission: number;
  tips: number;
}

export function summarizePerformance(rows: StaffPerformanceMetrics[]): PerformanceTotals {
  return rows.reduce(
    (acc, row) => ({
      revenue: acc.revenue + Number.parseFloat(row.revenue_generated),
      appointments: acc.appointments + row.appointments_completed,
      commission: acc.commission + Number.parseFloat(row.commission_earned),
      tips: acc.tips + Number.parseFloat(row.tips_earned),
    }),
    { revenue: 0, appointments: 0, commission: 0, tips: 0 },
  );
}

export function toEarningsChartData(rows: StaffPerformanceMetrics[]) {
  return rows.map((row) => ({
    name: row.staff_name,
    revenue: Number.parseFloat(row.revenue_generated),
    commission: Number.parseFloat(row.commission_earned),
    tips: Number.parseFloat(row.tips_earned),
  }));
}

export function toAppointmentsChartData(rows: StaffPerformanceMetrics[]) {
  return rows.map((row) => ({
    name: row.staff_name,
    completed: row.appointments_completed,
  }));
}

export function staffMetricToRows(metric: StaffPerformanceMetrics): StaffPerformanceMetrics[] {
  return [metric];
}
