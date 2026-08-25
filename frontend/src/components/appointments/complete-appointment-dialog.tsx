"use client";

import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { formatCurrency } from "@/lib/format";
import type { Appointment } from "@/types/api";

interface CompleteAppointmentDialogProps {
  open: boolean;
  appointment?: Appointment;
  loading?: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => Promise<void>;
}

export function CompleteAppointmentDialog({
  open,
  appointment,
  loading,
  onOpenChange,
  onConfirm,
}: CompleteAppointmentDialogProps) {
  const total = appointment?.services.reduce((sum, service) => sum + Number.parseFloat(service.price), 0) ?? 0;

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Complete appointment"
      description={
        appointment
          ? `Close the visit for ${appointment.customer_name} with ${appointment.staff_name}? An invoice will be created.`
          : "Close this visit? An invoice will be created."
      }
    >
      <div className="space-y-4">
        {appointment ? (
          <p className="text-sm text-muted-foreground">
            Services total {formatCurrency(total)}. You can record payment next.
          </p>
        ) : null}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="outline" disabled={loading} onClick={() => onOpenChange(false)}>
            Keep open
          </Button>
          <Button
            type="button"
            disabled={loading || !appointment}
            onClick={async () => {
              await onConfirm();
              onOpenChange(false);
            }}
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Completing
              </>
            ) : (
              "Complete visit"
            )}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
