"use client";

import { Pencil } from "lucide-react";

import { PermissionGate } from "@/components/auth/permission-gate";
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
import type { Tip } from "@/types/tips";

interface TipsTableProps {
  tips: Tip[];
  loading?: boolean;
  onEdit: (tip: Tip) => void;
}

export function TipsTable({ tips, loading, onEdit }: TipsTableProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <Skeleton key={index} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (tips.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border py-12 text-center">
        <p className="text-sm font-medium">No tips found</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Record discretionary tips against active appointments.
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
          <TableHead>Amount</TableHead>
          <TableHead>Notes</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {tips.map((tip) => (
          <TableRow key={tip.id}>
            <TableCell>
              <div>
                <p className="font-medium">{formatShortDate(tip.created_at.slice(0, 10))}</p>
                <p className="text-xs text-muted-foreground">{formatDateTimeLabel(tip.created_at)}</p>
              </div>
            </TableCell>
            <TableCell>{tip.staff_name}</TableCell>
            <TableCell className="font-medium">{formatCurrency(tip.amount)}</TableCell>
            <TableCell className="max-w-xs truncate text-muted-foreground">{tip.notes || "—"}</TableCell>
            <TableCell className="text-right">
              <PermissionGate permissions={["tips:write"]}>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  aria-label="Edit tip"
                  onClick={() => onEdit(tip)}
                >
                  <Pencil className="h-4 w-4" />
                </Button>
              </PermissionGate>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
