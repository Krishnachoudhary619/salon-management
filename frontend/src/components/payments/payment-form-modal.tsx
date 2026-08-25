"use client";

import { Dialog } from "@/components/ui/dialog";
import { PaymentForm } from "@/components/payments/payment-form";
import type { PaymentFormValues } from "@/lib/schemas/payment";
import type { Appointment } from "@/types/api";

interface PaymentFormModalProps {
  open: boolean;
  appointments: Appointment[];
  loading?: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (values: PaymentFormValues) => Promise<void>;
}

export function PaymentFormModal({
  open,
  appointments,
  loading,
  onOpenChange,
  onSubmit,
}: PaymentFormModalProps) {
  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Record payment"
      description="Record a CASH, CARD, or UPI payment against a completed appointment invoice."
      className="max-w-lg"
    >
      <PaymentForm
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
