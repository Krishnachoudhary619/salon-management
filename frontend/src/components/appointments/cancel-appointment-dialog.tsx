"use client";

import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";

interface CancelAppointmentDialogProps {
  open: boolean;
  customerName?: string;
  loading?: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => Promise<void>;
}

export function CancelAppointmentDialog({
  open,
  customerName,
  loading,
  onOpenChange,
  onConfirm,
}: CancelAppointmentDialogProps) {
  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Cancel appointment"
      description={
        customerName
          ? `Cancel the appointment for ${customerName}? This action cannot be undone.`
          : "Cancel this appointment? This action cannot be undone."
      }
    >
      <div className="flex justify-end gap-2">
        <Button type="button" variant="outline" disabled={loading} onClick={() => onOpenChange(false)}>
          Keep appointment
        </Button>
        <Button
          type="button"
          variant="destructive"
          disabled={loading}
          onClick={async () => {
            await onConfirm();
            onOpenChange(false);
          }}
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Cancelling
            </>
          ) : (
            "Cancel appointment"
          )}
        </Button>
      </div>
    </Dialog>
  );
}
