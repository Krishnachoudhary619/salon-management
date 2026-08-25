"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCurrency } from "@/lib/format";
import type { StaffPerformanceMetrics } from "@/types/performance";

interface PerformanceTableProps {
  rows: StaffPerformanceMetrics[];
  loading?: boolean;
  showStaffColumn?: boolean;
}

export function PerformanceTable({ rows, loading, showStaffColumn = true }: PerformanceTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Performance breakdown</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, index) => (
              <Skeleton key={index} className="h-10 w-full" />
            ))}
          </div>
        ) : rows.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">No performance data for this period</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                {showStaffColumn ? <TableHead>Staff</TableHead> : null}
                <TableHead className="text-right">Revenue</TableHead>
                <TableHead className="text-right">Appointments</TableHead>
                <TableHead className="text-right">Commission</TableHead>
                <TableHead className="text-right">Tips</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row) => (
                <TableRow key={row.staff_id}>
                  {showStaffColumn ? (
                    <TableCell className="font-medium">{row.staff_name}</TableCell>
                  ) : null}
                  <TableCell className="text-right">{formatCurrency(row.revenue_generated)}</TableCell>
                  <TableCell className="text-right">{row.appointments_completed}</TableCell>
                  <TableCell className="text-right">{formatCurrency(row.commission_earned)}</TableCell>
                  <TableCell className="text-right">{formatCurrency(row.tips_earned)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
