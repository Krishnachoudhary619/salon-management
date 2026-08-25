"use client";

import { Loader2 } from "lucide-react";

import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface DeactivateStaffDialogProps {
  open: boolean;
  staffName?: string;
  loading?: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => Promise<void>;
}

export function DeactivateStaffDialog({
  open,
  staffName,
  loading,
  onOpenChange,
  onConfirm,
}: DeactivateStaffDialogProps) {
  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Deactivate staff member"
      description={
        staffName
          ? `"${staffName}" will be set to inactive and their login will be disabled.`
          : "This staff member will be set to inactive and their login disabled."
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
