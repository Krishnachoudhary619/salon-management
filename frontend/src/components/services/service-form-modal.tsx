"use client";

import { Dialog } from "@/components/ui/dialog";
import { ServiceForm } from "@/components/services/service-form";
import type { ServiceFormValues } from "@/lib/schemas/service";
import type { Service } from "@/types/services";

interface ServiceFormModalProps {
  open: boolean;
  mode: "create" | "edit";
  service?: Service;
  loading?: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (values: ServiceFormValues) => Promise<void>;
}

export function ServiceFormModal({
  open,
  mode,
  service,
  loading,
  onOpenChange,
  onSubmit,
}: ServiceFormModalProps) {
  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={mode === "create" ? "Create service" : "Edit service"}
      description={
        mode === "create"
          ? "Add a new bookable service to the catalog."
          : "Update service details. Changes apply to future bookings only."
      }
    >
      <ServiceForm
        mode={mode}
        service={service}
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
