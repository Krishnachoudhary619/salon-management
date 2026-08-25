"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCurrency } from "@/lib/format";
import { getReportPeriodDescription } from "@/lib/reports/period-utils";
import type { ReportPeriod } from "@/types/reports";
import type { StaffPerformanceMetrics } from "@/types/performance";

interface StaffPerformanceReportPanelProps {
  rows: StaffPerformanceMetrics[];
  period: ReportPeriod;
  loading?: boolean;
}

function summarizeTeam(rows: StaffPerformanceMetrics[]) {
  return rows.reduce(
    (acc, row) => ({
      revenue: acc.revenue + Number.parseFloat(row.revenue_generated),
      customers: acc.customers + row.customers_served,
      appointments: acc.appointments + row.appointments_completed,
      tips: acc.tips + Number.parseFloat(row.tips_earned),
      commission: acc.commission + Number.parseFloat(row.commission_earned),
    }),
    { revenue: 0, customers: 0, appointments: 0, tips: 0, commission: 0 },
  );
}

export function StaffPerformanceReportPanel({
  rows,
  period,
  loading,
}: StaffPerformanceReportPanelProps) {
  const totals = summarizeTeam(rows);

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Revenue</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">{formatCurrency(totals.revenue)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Customers</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">{totals.customers}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Appointments</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">{totals.appointments}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Tips</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">{formatCurrency(totals.tips)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Commission</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">{formatCurrency(totals.commission)}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Staff performance</CardTitle>
          <p className="text-sm text-muted-foreground">{getReportPeriodDescription(period)}</p>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="py-8 text-center text-sm text-muted-foreground">Loading performance data…</p>
          ) : rows.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">No staff performance data for this period</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Staff</TableHead>
                  <TableHead className="text-right">Revenue</TableHead>
                  <TableHead className="text-right">Customers</TableHead>
                  <TableHead className="text-right">Appointments</TableHead>
                  <TableHead className="text-right">Tips</TableHead>
                  <TableHead className="text-right">Commission</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((row) => (
                  <TableRow key={row.staff_id}>
                    <TableCell className="font-medium">{row.staff_name}</TableCell>
                    <TableCell className="text-right">{formatCurrency(row.revenue_generated)}</TableCell>
                    <TableCell className="text-right">{row.customers_served}</TableCell>
                    <TableCell className="text-right">{row.appointments_completed}</TableCell>
                    <TableCell className="text-right">{formatCurrency(row.tips_earned)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(row.commission_earned)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
