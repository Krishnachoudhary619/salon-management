"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { usePermissions } from "@/hooks/use-permissions";
import { formatShortDate, formatTime } from "@/lib/format";
import type { Appointment } from "@/types/api";
import type { StaffMember } from "@/types/staff";

interface ConfirmAppointmentDialogProps {
  open: boolean;
  appointment?: Appointment;
  staff: StaffMember[];
  loading?: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: (staffId: string) => Promise<void>;
}

export function ConfirmAppointmentDialog({
  open,
  appointment,
  staff,
  loading,
  onOpenChange,
  onConfirm,
}: ConfirmAppointmentDialogProps) {
  const { can } = usePermissions();
  const canAssignAny = can("appointments:write");
  const [staffId, setStaffId] = useState("");

  useEffect(() => {
    if (open) {
      setStaffId(appointment?.staff_id ?? "");
    }
  }, [open, appointment?.staff_id]);

  if (!appointment) {
    return null;
  }

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Confirm appointment"
      description={`Assign a stylist and confirm ${appointment.customer_name} for ${formatShortDate(appointment.appointment_date)} at ${formatTime(appointment.start_time)}.`}
    >
      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="confirm-staff">Staff</Label>
          <select
            id="confirm-staff"
            value={staffId}
            disabled={!canAssignAny}
            onChange={(event) => setStaffId(event.target.value)}
            className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="">Select a staff member</option>
            {staff.map((member) => (
              <option key={member.id} value={member.id}>
                {member.name}
              </option>
            ))}
          </select>
        </div>
        <div className="flex justify-end gap-2">
          <Button type="button" variant="outline" disabled={loading} onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            type="button"
            disabled={loading || !staffId}
            onClick={async () => {
              await onConfirm(staffId);
              onOpenChange(false);
            }}
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Confirming
              </>
            ) : (
              "Confirm appointment"
            )}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
