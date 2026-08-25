"use client";

import { Pencil, Trash2 } from "lucide-react";

import { PermissionGate } from "@/components/auth/permission-gate";
import { StaffStatusBadge } from "@/components/staff/staff-status-badge";
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
import { formatCommission } from "@/lib/schemas/staff";
import { formatShortDate } from "@/lib/format";
import type { StaffMember } from "@/types/staff";

interface StaffTableProps {
  staff: StaffMember[];
  loading?: boolean;
  onEdit: (member: StaffMember) => void;
  onDeactivate: (member: StaffMember) => void;
}

export function StaffTable({ staff, loading, onEdit, onDeactivate }: StaffTableProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <Skeleton key={index} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (staff.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border py-12 text-center">
        <p className="text-sm font-medium">No staff found</p>
        <p className="mt-1 text-sm text-muted-foreground">Try adjusting your search or add a team member.</p>
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Designation</TableHead>
          <TableHead>Commission</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Phone</TableHead>
          <TableHead>Joined</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {staff.map((member) => (
          <TableRow key={member.id}>
            <TableCell>
              <div>
                <p className="font-medium">{member.name}</p>
                {member.email ? (
                  <p className="mt-0.5 text-xs text-muted-foreground">{member.email}</p>
                ) : null}
              </div>
            </TableCell>
            <TableCell>{member.designation}</TableCell>
            <TableCell>{formatCommission(member.commission_percentage)}</TableCell>
            <TableCell>
              <StaffStatusBadge status={member.status} />
            </TableCell>
            <TableCell>{member.phone}</TableCell>
            <TableCell>{formatShortDate(member.joining_date)}</TableCell>
            <TableCell className="text-right">
              <div className="flex justify-end gap-1">
                <PermissionGate permissions={["staff:write"]}>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    aria-label={`Edit ${member.name}`}
                    onClick={() => onEdit(member)}
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                </PermissionGate>
                <PermissionGate permissions={["staff:delete"]}>
                  {member.status !== "INACTIVE" ? (
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      aria-label={`Deactivate ${member.name}`}
                      onClick={() => onDeactivate(member)}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  ) : null}
                </PermissionGate>
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
