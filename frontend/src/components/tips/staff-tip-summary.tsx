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
import { formatMonthLabel } from "@/lib/tips/summary-utils";
import type { StaffTipSummary } from "@/types/tips";
import type { StaffPerformanceMetrics } from "@/types/performance";

interface StaffTipSummaryProps {
  monthKey: string;
  listSummary: StaffTipSummary;
  teamMetrics?: StaffPerformanceMetrics[];
  staffMetric?: StaffPerformanceMetrics;
  loading?: boolean;
  error?: unknown;
  onRetry?: () => void;
  showTeamBreakdown?: boolean;
}

export function StaffTipSummaryPanel({
  monthKey,
  listSummary,
  teamMetrics,
  staffMetric,
  loading,
  error,
  onRetry,
  showTeamBreakdown = false,
}: StaffTipSummaryProps) {
  const tipTotal = staffMetric
    ? Number.parseFloat(staffMetric.tips_earned)
    : teamMetrics
      ? teamMetrics.reduce((sum, item) => sum + Number.parseFloat(item.tips_earned), 0)
      : listSummary.tipTotal;

  const count = staffMetric ? undefined : listSummary.count;

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">{formatMonthLabel(monthKey)} tip summary</h2>
        <p className="text-sm text-muted-foreground">Discretionary tips earned in the selected period.</p>
      </div>

      {loading ? <LoadingSpinner label="Loading tip summary" /> : null}
      {error ? (
        <ErrorDisplay error={error} title="Unable to load performance summary" onRetry={onRetry} />
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Tips earned</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">{formatCurrency(tipTotal)}</p>
          </CardContent>
        </Card>
        {count !== undefined ? (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Tip entries</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-semibold">{count}</p>
            </CardContent>
          </Card>
        ) : null}
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
                  <TableHead>Tips earned</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {teamMetrics.map((item) => (
                  <TableRow key={item.staff_id}>
                    <TableCell className="font-medium">{item.staff_name}</TableCell>
                    <TableCell>{formatCurrency(item.tips_earned)}</TableCell>
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
