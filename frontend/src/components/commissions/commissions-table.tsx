"use client";

import { Eye } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCurrency, formatDateTimeLabel, formatShortDate } from "@/lib/format";
import { formatCommission } from "@/lib/schemas/staff";
import type { Commission } from "@/types/commissions";

interface CommissionsTableProps {
  commissions: Commission[];
  loading?: boolean;
  onView: (commission: Commission) => void;
}

export function CommissionsTable({ commissions, loading, onView }: CommissionsTableProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <Skeleton key={index} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (commissions.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border py-12 text-center">
        <p className="text-sm font-medium">No commissions found</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Commissions appear after appointments are completed and fully paid.
        </p>
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Date</TableHead>
          <TableHead>Staff</TableHead>
          <TableHead>Revenue</TableHead>
          <TableHead>Rate</TableHead>
          <TableHead>Commission</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {commissions.map((commission) => (
          <TableRow key={commission.id}>
            <TableCell>
              <div>
                <p className="font-medium">{formatShortDate(commission.created_at.slice(0, 10))}</p>
                <p className="text-xs text-muted-foreground">
                  {formatDateTimeLabel(commission.created_at)}
                </p>
              </div>
            </TableCell>
            <TableCell>{commission.staff_name}</TableCell>
            <TableCell>{formatCurrency(commission.service_revenue)}</TableCell>
            <TableCell>{formatCommission(commission.commission_percentage)}</TableCell>
            <TableCell className="font-medium">{formatCurrency(commission.commission_amount)}</TableCell>
            <TableCell className="text-right">
              <Button
                type="button"
                variant="ghost"
                size="icon"
                aria-label="View commission details"
                onClick={() => onView(commission)}
              >
                <Eye className="h-4 w-4" />
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
