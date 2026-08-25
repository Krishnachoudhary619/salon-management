"use client";

import { Dialog } from "@/components/ui/dialog";
import { BookingWizard } from "@/components/appointments/booking-wizard";
import type { BookingDraft } from "@/lib/schemas/booking-wizard";
import { toBookingAppointmentCreatePayload } from "@/lib/schemas/booking-wizard";
import type { Customer } from "@/types/customers";
import type { Service } from "@/types/services";
import type { StaffMember } from "@/types/staff";

interface BookingWizardModalProps {
  open: boolean;
  customers: Customer[];
  staff: StaffMember[];
  services: Service[];
  defaults?: Partial<BookingDraft>;
  loading?: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (payload: ReturnType<typeof toBookingAppointmentCreatePayload>) => Promise<void>;
}

export function BookingWizardModal({
  open,
  customers,
  staff,
  services,
  defaults,
  loading,
  onOpenChange,
  onSubmit,
}: BookingWizardModalProps) {
  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Book appointment"
      description="Follow the steps to create a new booking with availability validation."
      className="max-w-2xl"
    >
      <BookingWizard
        customers={customers}
        staff={staff}
        services={services}
        defaults={defaults}
        loading={loading}
        onCancel={() => onOpenChange(false)}
        onSubmit={async (payload) => {
          await onSubmit(payload);
          onOpenChange(false);
        }}
      />
    </Dialog>
  );
}
