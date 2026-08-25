"use client";

import { Dialog } from "@/components/ui/dialog";
import { RescheduleForm } from "@/components/appointments/reschedule-form";
import type { RescheduleFormValues } from "@/lib/schemas/appointment";
import type { Appointment } from "@/types/api";
import type { StaffMember } from "@/types/staff";

interface RescheduleModalProps {
  open: boolean;
  appointment?: Appointment;
  staff: StaffMember[];
  loading?: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (values: RescheduleFormValues) => Promise<void>;
}

export function RescheduleModal({
  open,
  appointment,
  staff,
  loading,
  onOpenChange,
  onSubmit,
}: RescheduleModalProps) {
  if (!appointment) {
    return null;
  }

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Reschedule appointment"
      description={`Move ${appointment.customer_name}'s appointment to a new date or time.`}
    >
      <RescheduleForm
        appointment={appointment}
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
