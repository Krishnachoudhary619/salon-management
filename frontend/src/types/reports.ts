export type ReportType = "revenue" | "appointments" | "staff_performance";

export type ReportPeriod = "daily" | "weekly" | "monthly";

export interface ReportDateRange {
  start_date: string;
  end_date: string;
}

export interface RevenueReportRow {
  period: string;
  label: string;
  revenue: number;
}

export interface AppointmentReportRow {
  period: string;
  label: string;
  total: number;
  completed: number;
  cancelled: number;
}
