"use client";

import { Dialog } from "@/components/ui/dialog";
import { TipEditForm } from "@/components/tips/tip-edit-form";
import type { TipEditValues } from "@/lib/schemas/tip";
import type { Tip } from "@/types/tips";

interface TipEditModalProps {
  open: boolean;
  tip?: Tip;
  loading?: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (values: TipEditValues) => Promise<void>;
}

export function TipEditModal({ open, tip, loading, onOpenChange, onSubmit }: TipEditModalProps) {
  if (!tip) {
    return null;
  }

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Edit tip"
      description="Update the tip amount or notes. Commission is not recalculated."
      className="max-w-lg"
    >
      <TipEditForm
        tip={tip}
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
