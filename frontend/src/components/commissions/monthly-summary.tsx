"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorDisplay } from "@/components/feedback/error-display";
import { LoadingSpinner } from "@/components/feedback/loading-state";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCurrency } from "@/lib/format";
import { formatMonthLabel } from "@/lib/commissions/summary-utils";
import type { MonthlyCommissionSummary } from "@/types/commissions";
import type { StaffPerformanceMetrics } from "@/types/performance";

interface MonthlySummaryProps {
  monthKey: string;
  listSummary: MonthlyCommissionSummary;
  teamMetrics?: StaffPerformanceMetrics[];
  staffMetric?: StaffPerformanceMetrics;
  loading?: boolean;
  error?: unknown;
  onRetry?: () => void;
  showTeamBreakdown?: boolean;
}

export function MonthlySummary({
  monthKey,
  listSummary,
  teamMetrics,
  staffMetric,
  loading,
  error,
  onRetry,
  showTeamBreakdown = false,
}: MonthlySummaryProps) {
  const commissionTotal = staffMetric
    ? Number.parseFloat(staffMetric.commission_earned)
    : teamMetrics
      ? teamMetrics.reduce((sum, item) => sum + Number.parseFloat(item.commission_earned), 0)
      : listSummary.commissionTotal;

  const revenueTotal = staffMetric
    ? Number.parseFloat(staffMetric.revenue_generated)
    : teamMetrics
      ? teamMetrics.reduce((sum, item) => sum + Number.parseFloat(item.revenue_generated), 0)
      : listSummary.revenueTotal;

  const count = staffMetric
    ? staffMetric.appointments_completed
    : teamMetrics
      ? teamMetrics.reduce((sum, item) => sum + item.appointments_completed, 0)
      : listSummary.count;

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">{formatMonthLabel(monthKey)} summary</h2>
        <p className="text-sm text-muted-foreground">Commission earnings for the selected period.</p>
      </div>

      {loading ? <LoadingSpinner label="Loading monthly summary" /> : null}
      {error ? (
        <ErrorDisplay error={error} title="Unable to load performance summary" onRetry={onRetry} />
      ) : null}

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Commission earned</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">{formatCurrency(commissionTotal)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Service revenue</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">{formatCurrency(revenueTotal)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Appointments</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">{count}</p>
          </CardContent>
        </Card>
      </div>

      {showTeamBreakdown && teamMetrics && teamMetrics.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">By staff member</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Staff</TableHead>
                  <TableHead>Revenue</TableHead>
                  <TableHead>Commission</TableHead>
                  <TableHead>Appointments</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {teamMetrics.map((item) => (
                  <TableRow key={item.staff_id}>
                    <TableCell className="font-medium">{item.staff_name}</TableCell>
                    <TableCell>{formatCurrency(item.revenue_generated)}</TableCell>
                    <TableCell>{formatCurrency(item.commission_earned)}</TableCell>
                    <TableCell>{item.appointments_completed}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
