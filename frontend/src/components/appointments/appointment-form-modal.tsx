"use client";

import { Dialog } from "@/components/ui/dialog";
import { AppointmentForm } from "@/components/appointments/appointment-form";
import type { AppointmentFormValues, AppointmentEditValues } from "@/lib/schemas/appointment";
import type { Appointment } from "@/types/api";
import type { Customer } from "@/types/customers";
import type { Service } from "@/types/services";
import type { StaffMember } from "@/types/staff";

interface AppointmentFormModalProps {
  open: boolean;
  mode: "create" | "edit";
  appointment?: Appointment;
  customers: Customer[];
  staff: StaffMember[];
  services: Service[];
  defaults?: Partial<AppointmentFormValues>;
  loading?: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (values: AppointmentFormValues | AppointmentEditValues) => Promise<void>;
}

export function AppointmentFormModal({
  open,
  mode,
  appointment,
  customers,
  staff,
  services,
  defaults,
  loading,
  onOpenChange,
  onSubmit,
}: AppointmentFormModalProps) {
  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={mode === "create" ? "Create appointment" : "Edit appointment"}
      description={
        mode === "create"
          ? "Book a new appointment for a customer."
          : "Update customer, staff, services, or notes."
      }
      className="max-w-2xl"
    >
      <AppointmentForm
        mode={mode}
        appointment={appointment}
        customers={customers}
        staff={staff}
        services={services}
        defaults={defaults}
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
