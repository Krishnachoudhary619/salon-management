"use client";

import { Dialog } from "@/components/ui/dialog";
import { TipForm } from "@/components/tips/tip-form";
import type { TipFormValues } from "@/lib/schemas/tip";
import type { Appointment } from "@/types/api";

interface TipFormModalProps {
  open: boolean;
  appointments: Appointment[];
  loading?: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (values: TipFormValues) => Promise<void>;
}

export function TipFormModal({
  open,
  appointments,
  loading,
  onOpenChange,
  onSubmit,
}: TipFormModalProps) {
  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Add tip"
      description="Record a discretionary tip for the appointment staff member."
      className="max-w-lg"
    >
      <TipForm
        appointments={appointments}
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
