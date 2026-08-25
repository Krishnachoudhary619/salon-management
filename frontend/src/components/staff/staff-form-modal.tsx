"use client";

import { Dialog } from "@/components/ui/dialog";
import { StaffForm } from "@/components/staff/staff-form";
import type { StaffCreateFormValues, StaffEditFormValues } from "@/lib/schemas/staff";
import type { StaffMember } from "@/types/staff";

interface StaffFormModalProps {
  open: boolean;
  mode: "create" | "edit";
  staff?: StaffMember;
  loading?: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (values: StaffCreateFormValues | StaffEditFormValues) => Promise<void>;
}

export function StaffFormModal({
  open,
  mode,
  staff,
  loading,
  onOpenChange,
  onSubmit,
}: StaffFormModalProps) {
  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={mode === "create" ? "Add staff member" : "Edit staff member"}
      description={
        mode === "create"
          ? "Create a staff profile and linked login account."
          : "Update staff details. Commission changes require admin access."
      }
      className="max-w-2xl"
    >
      <StaffForm
        mode={mode}
        staff={staff}
        loading={loading}
        onCancel={() => onOpenChange(false)}
        onSubmit={async (values) => {
          await onSubmit(values);
          onOpenChange(false);
        }}
      />
    </Dialog>
  );
}
