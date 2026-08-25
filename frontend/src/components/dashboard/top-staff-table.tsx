"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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
import type { TopPerformer } from "@/types/dashboard";

interface TopStaffTableProps {
  staff: TopPerformer[];
  loading?: boolean;
}

export function TopStaffTable({ staff, loading }: TopStaffTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Top Staff</CardTitle>
        <CardDescription>Highest revenue performers this month</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, index) => (
              <Skeleton key={index} className="h-10 w-full" />
            ))}
          </div>
        ) : staff.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">No staff performance data yet</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Staff</TableHead>
                <TableHead>Revenue</TableHead>
                <TableHead>Completed</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {staff.map((member, index) => (
                <TableRow key={member.staff_id}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <span className="flex h-7 w-7 items-center justify-center rounded-full bg-muted text-xs font-semibold">
                        {index + 1}
                      </span>
                      <span className="font-medium">{member.staff_name}</span>
                    </div>
                  </TableCell>
                  <TableCell>{formatCurrency(member.revenue)}</TableCell>
                  <TableCell>{member.appointments_completed}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
