"use client";

import { useMemo, useState } from "react";

import { AppointmentsReportPanel } from "@/components/reports/appointments-report-panel";
import { ExportCsvButton } from "@/components/reports/export-csv-button";
import { ReportPeriodFilter } from "@/components/reports/report-period-filter";
import { ReportTypeTabs } from "@/components/reports/report-type-tabs";
import { RevenueReportPanel } from "@/components/reports/revenue-report-panel";
import { StaffPerformanceReportPanel } from "@/components/reports/staff-performance-report-panel";
import { ErrorDisplay } from "@/components/feedback/error-display";
import {
  useAppointmentsReport,
  useRevenueReport,
  useStaffPerformanceReport,
} from "@/hooks/use-reports";
import {
  exportAppointmentsReportCsv,
  exportRevenueReportCsv,
  exportStaffPerformanceReportCsv,
  getReportExportLabel,
} from "@/lib/reports/csv-export";
import { getReportPeriodDescription } from "@/lib/reports/period-utils";
import { toast } from "@/lib/toast";
import type { ReportPeriod, ReportType } from "@/types/reports";

export function ReportsView() {
  const [reportType, setReportType] = useState<ReportType>("revenue");
  const [period, setPeriod] = useState<ReportPeriod>("daily");

  const revenueQuery = useRevenueReport(period, reportType === "revenue");
  const appointmentsQuery = useAppointmentsReport(period, reportType === "appointments");
  const staffPerformanceQuery = useStaffPerformanceReport(period, reportType === "staff_performance");

  const activeQuery =
    reportType === "revenue"
      ? revenueQuery
      : reportType === "appointments"
        ? appointmentsQuery
        : staffPerformanceQuery;

  const exportDisabled = useMemo(() => {
    if (activeQuery.isLoading) {
      return true;
    }
    if (reportType === "revenue") {
      return revenueQuery.rows.length === 0;
    }
    if (reportType === "appointments") {
      return appointmentsQuery.rows.length === 0;
    }
    return staffPerformanceQuery.rows.length === 0;
  }, [
    activeQuery.isLoading,
    reportType,
    revenueQuery.rows.length,
    appointmentsQuery.rows.length,
    staffPerformanceQuery.rows.length,
  ]);

  const handleExport = () => {
    try {
      if (reportType === "revenue") {
        exportRevenueReportCsv(revenueQuery.rows, period);
      } else if (reportType === "appointments") {
        exportAppointmentsReportCsv(appointmentsQuery.rows, period);
      } else {
        exportStaffPerformanceReportCsv(staffPerformanceQuery.rows, period, staffPerformanceQuery.range);
      }
      toast.success("Report exported as CSV");
    } catch (error) {
      toast.fromError(error, "Unable to export report");
    }
  };

  if (activeQuery.isError) {
    return (
      <ErrorDisplay
        error={activeQuery.error}
        title="Unable to load report"
        onRetry={() => activeQuery.refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Reports</h1>
          <p className="text-sm text-muted-foreground">
            Revenue, appointment volume, and staff performance with CSV export.
          </p>
        </div>
        <ExportCsvButton
          label={getReportExportLabel(reportType, period)}
          disabled={exportDisabled}
          onExport={handleExport}
        />
      </div>

      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <ReportTypeTabs value={reportType} onChange={setReportType} />
        <ReportPeriodFilter value={period} onChange={setPeriod} />
      </div>

      <p className="text-sm text-muted-foreground">{getReportPeriodDescription(period)}</p>

      {reportType === "revenue" ? (
        <RevenueReportPanel rows={revenueQuery.rows} period={period} loading={revenueQuery.isLoading} />
      ) : null}

      {reportType === "appointments" ? (
        <AppointmentsReportPanel
          rows={appointmentsQuery.rows}
          period={period}
          loading={appointmentsQuery.isLoading}
        />
      ) : null}

      {reportType === "staff_performance" ? (
        <StaffPerformanceReportPanel
          rows={staffPerformanceQuery.rows}
          period={period}
          loading={staffPerformanceQuery.isLoading}
        />
      ) : null}
    </div>
  );
}
