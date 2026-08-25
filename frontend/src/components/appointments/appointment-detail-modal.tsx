"use client";

import { CalendarClock, Check, CheckCircle, Pencil, XCircle } from "lucide-react";

import { AppointmentStatusBadge } from "@/components/dashboard/appointment-status-badge";
import { PermissionGate } from "@/components/auth/permission-gate";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import {
  canCancel,
  canComplete,
  canConfirm,
  canEdit,
  canReschedule,
  getNextVisitStatus,
  getVisitActionLabel,
} from "@/lib/appointments/status-colors";
import { formatCurrency, formatShortDate, formatTime } from "@/lib/format";
import type { Appointment, AppointmentStatus } from "@/types/api";

interface AppointmentDetailModalProps {
  open: boolean;
  appointment?: Appointment;
  loading?: boolean;
  onOpenChange: (open: boolean) => void;
  onEdit: (appointment: Appointment) => void;
  onConfirm: (appointment: Appointment) => void;
  onAdvance: (appointment: Appointment, status: AppointmentStatus) => void;
  onComplete: (appointment: Appointment) => void;
  onReschedule: (appointment: Appointment) => void;
  onCancel: (appointment: Appointment) => void;
}

export function AppointmentDetailModal({
  open,
  appointment,
  loading,
  onOpenChange,
  onEdit,
  onConfirm,
  onAdvance,
  onComplete,
  onReschedule,
  onCancel,
}: AppointmentDetailModalProps) {
  if (!appointment) {
    return null;
  }

  const editable = canEdit(appointment.status);
  const confirmable = canConfirm(appointment.status);
  const completeable = canComplete(appointment.status);
  const nextStatus = getNextVisitStatus(appointment.status);
  const nextLabel = getVisitActionLabel(appointment.status);
  const reschedulable = canReschedule(appointment.status);
  const cancellable = canCancel(appointment.status);

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Appointment details"
      description={`${appointment.customer_name} with ${appointment.staff_name}`}
      className="max-w-lg"
    >
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <AppointmentStatusBadge status={appointment.status} />
          <span className="text-sm text-muted-foreground">{appointment.duration_minutes} min</span>
        </div>

        <dl className="grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-muted-foreground">Date</dt>
            <dd className="font-medium">{formatShortDate(appointment.appointment_date)}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Time</dt>
            <dd className="font-medium">
              {formatTime(appointment.start_time)} – {formatTime(appointment.end_time)}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Customer</dt>
            <dd className="font-medium">{appointment.customer_name}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Staff</dt>
            <dd className="font-medium">{appointment.staff_name}</dd>
          </div>
        </dl>

        <div>
          <p className="text-sm text-muted-foreground">Services</p>
          <ul className="mt-2 space-y-2">
            {appointment.services.map((service) => (
              <li
                key={service.id}
                className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-sm"
              >
                <span>{service.service_name}</span>
                <span className="text-muted-foreground">
                  {service.duration_minutes} min · {formatCurrency(service.price)}
                </span>
              </li>
            ))}
          </ul>
        </div>

        {appointment.notes ? (
          <div>
            <p className="text-sm text-muted-foreground">Notes</p>
            <p className="mt-1 whitespace-pre-wrap text-sm">{appointment.notes}</p>
          </div>
        ) : null}

        <PermissionGate permissions={["appointments:write", "appointments:write_own"]} any>
          <div className="flex flex-wrap justify-end gap-2 border-t border-border pt-4">
            {confirmable ? (
              <Button type="button" disabled={loading} onClick={() => onConfirm(appointment)}>
                <Check className="h-4 w-4" />
                Confirm
              </Button>
            ) : null}
            {completeable ? (
              <Button type="button" disabled={loading} onClick={() => onComplete(appointment)}>
                <CheckCircle className="h-4 w-4" />
                Complete
              </Button>
            ) : nextStatus && nextLabel ? (
              <Button type="button" disabled={loading} onClick={() => onAdvance(appointment, nextStatus)}>
                <Check className="h-4 w-4" />
                {nextLabel}
              </Button>
            ) : null}
            {editable ? (
              <Button type="button" variant="outline" disabled={loading} onClick={() => onEdit(appointment)}>
                <Pencil className="h-4 w-4" />
                Edit
              </Button>
            ) : null}
            {reschedulable ? (
              <Button
                type="button"
                variant="outline"
                disabled={loading}
                onClick={() => onReschedule(appointment)}
              >
                <CalendarClock className="h-4 w-4" />
                Reschedule
              </Button>
            ) : null}
            {cancellable ? (
              <Button
                type="button"
                variant="destructive"
                disabled={loading}
                onClick={() => onCancel(appointment)}
              >
                <XCircle className="h-4 w-4" />
                Cancel
              </Button>
            ) : null}
          </div>
        </PermissionGate>
      </div>
    </Dialog>
  );
}
