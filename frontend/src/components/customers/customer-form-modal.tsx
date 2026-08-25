"use client";

import { Dialog } from "@/components/ui/dialog";
import { CustomerForm } from "@/components/customers/customer-form";
import type { CustomerFormValues } from "@/lib/schemas/customer";

interface CustomerFormModalProps {
  open: boolean;
  loading?: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (values: CustomerFormValues) => Promise<void>;
}

export function CustomerFormModal({ open, loading, onOpenChange, onSubmit }: CustomerFormModalProps) {
  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Add customer"
      description="Register a walk-in or new customer before booking."
    >
      <CustomerForm
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
