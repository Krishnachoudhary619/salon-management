"use client";

import { Trophy } from "lucide-react";

import { getInitials } from "@/components/dashboard/dashboard-utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency } from "@/lib/format";
import type { TopPerformer } from "@/types/dashboard";

interface TopStaffTableProps {
  staff: TopPerformer[];
  loading?: boolean;
}

export function TopStaffTable({ staff, loading }: TopStaffTableProps) {
  const maxRevenue = Math.max(...staff.map((member) => Number.parseFloat(member.revenue) || 0), 1);

  return (
    <Card className="rounded-2xl border-border/70 shadow-none">
      <CardHeader className="pb-4">
        <CardTitle className="text-base font-semibold">Top staff</CardTitle>
        <CardDescription>Highest revenue this month</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, index) => (
              <Skeleton key={index} className="h-16 w-full rounded-xl" />
            ))}
          </div>
        ) : staff.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-xl bg-muted/40 px-4 py-10 text-center">
            <Trophy className="mb-3 h-8 w-8 text-muted-foreground/70" />
            <p className="text-sm text-muted-foreground">No staff performance data yet</p>
          </div>
        ) : (
          <ul className="space-y-4">
            {staff.map((member, index) => {
              const revenue = Number.parseFloat(member.revenue) || 0;
              const width = Math.max(8, Math.round((revenue / maxRevenue) * 100));
              return (
                <li key={member.staff_id} className="space-y-2">
                  <div className="flex items-center gap-3">
                    <span className="w-4 text-xs font-semibold text-muted-foreground">{index + 1}</span>
                    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-amber-50 text-xs font-semibold text-amber-800">
                      {getInitials(member.staff_name)}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-baseline justify-between gap-3">
                        <p className="truncate text-sm font-medium">{member.staff_name}</p>
                        <p className="shrink-0 text-sm font-semibold">{formatCurrency(member.revenue)}</p>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {member.appointments_completed} completed
                      </p>
                    </div>
                  </div>
                  <div className="ml-7 h-1.5 overflow-hidden rounded-full bg-muted">
                    <div className="h-full rounded-full bg-amber-400" style={{ width: `${width}%` }} />
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
