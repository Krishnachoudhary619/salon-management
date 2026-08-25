import type { AppointmentReportRow, ReportPeriod, ReportType, RevenueReportRow } from "@/types/reports";
import type { StaffPerformanceMetrics } from "@/types/performance";
import { REPORT_PERIOD_LABELS, REPORT_TYPE_LABELS } from "@/lib/reports/period-utils";

function escapeCsvValue(value: string | number) {
  const text = String(value);
  if (/[",\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

function buildCsv(headers: string[], rows: Array<Array<string | number>>) {
  return [headers, ...rows]
    .map((row) => row.map(escapeCsvValue).join(","))
    .join("\n");
}

function downloadCsv(filename: string, content: string) {
  const blob = new Blob([content], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function reportFilename(type: ReportType, period: ReportPeriod) {
  const stamp = new Date().toISOString().slice(0, 10);
  return `${type}-${period}-${stamp}.csv`;
}

export function exportRevenueReportCsv(rows: RevenueReportRow[], period: ReportPeriod) {
  const content = buildCsv(
    ["Period", "Label", "Revenue"],
    rows.map((row) => [row.period, row.label, row.revenue.toFixed(2)]),
  );
  downloadCsv(reportFilename("revenue", period), content);
}

export function exportAppointmentsReportCsv(rows: AppointmentReportRow[], period: ReportPeriod) {
  const content = buildCsv(
    ["Period", "Label", "Total", "Completed", "Cancelled"],
    rows.map((row) => [row.period, row.label, row.total, row.completed, row.cancelled]),
  );
  downloadCsv(reportFilename("appointments", period), content);
}

export function exportStaffPerformanceReportCsv(
  rows: StaffPerformanceMetrics[],
  period: ReportPeriod,
  range: { start_date: string; end_date: string },
) {
  const content = buildCsv(
    [
      "Staff",
      "Revenue Generated",
      "Customers Served",
      "Appointments Completed",
      "Tips Earned",
      "Commission Earned",
    ],
    rows.map((row) => [
      row.staff_name,
      row.revenue_generated,
      row.customers_served,
      row.appointments_completed,
      row.tips_earned,
      row.commission_earned,
    ]),
  );
  const filename = `staff-performance-${period}-${range.start_date}-to-${range.end_date}.csv`;
  downloadCsv(filename, content);
}

export function getReportExportLabel(type: ReportType, period: ReportPeriod) {
  return `Export ${REPORT_TYPE_LABELS[type]} (${REPORT_PERIOD_LABELS[period]})`;
}
