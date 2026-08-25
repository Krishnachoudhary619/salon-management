"use client";

import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";

interface DeactivateServiceDialogProps {
  open: boolean;
  serviceName?: string;
  loading?: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => Promise<void>;
}

export function DeactivateServiceDialog({
  open,
  serviceName,
  loading,
  onOpenChange,
  onConfirm,
}: DeactivateServiceDialogProps) {
  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Deactivate service"
      description={
        serviceName
          ? `"${serviceName}" will be hidden from new bookings. Existing appointments are not affected.`
          : "This service will be hidden from new bookings."
      }
    >
      <div className="flex justify-end gap-2">
        <Button type="button" variant="outline" disabled={loading} onClick={() => onOpenChange(false)}>
          Cancel
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
              Deactivating
            </>
          ) : (
            "Deactivate"
          )}
        </Button>
      </div>
    </Dialog>
  );
}
