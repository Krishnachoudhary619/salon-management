"use client";

import { CalendarClock } from "lucide-react";

import { PermissionGate } from "@/components/auth/permission-gate";
import { AppointmentStatusBadge } from "@/components/dashboard/appointment-status-badge";
import { getInitials } from "@/components/dashboard/dashboard-utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { canComplete, canConfirm, getNextVisitStatus, getVisitActionLabel } from "@/lib/appointments/status-colors";
import { formatShortDate, formatTime } from "@/lib/format";
import type { Appointment, AppointmentStatus } from "@/types/api";

interface UpcomingAppointmentsTableProps {
  appointments: Appointment[];
  loading?: boolean;
  onConfirm?: (appointment: Appointment) => void;
  onAdvance?: (appointment: Appointment, status: AppointmentStatus) => void;
  onComplete?: (appointment: Appointment) => void;
}

function AppointmentAction({
  appointment,
  onConfirm,
  onAdvance,
  onComplete,
}: Pick<UpcomingAppointmentsTableProps, "onConfirm" | "onAdvance" | "onComplete"> & {
  appointment: Appointment;
}) {
  const nextStatus = getNextVisitStatus(appointment.status);

  if (canConfirm(appointment.status) && onConfirm) {
    return (
      <Button type="button" size="sm" className="rounded-full" onClick={() => onConfirm(appointment)}>
        Confirm
      </Button>
    );
  }
  if (canComplete(appointment.status) && onComplete) {
    return (
      <Button type="button" size="sm" className="rounded-full" onClick={() => onComplete(appointment)}>
        Complete
      </Button>
    );
  }
  if (nextStatus && onAdvance) {
    return (
      <Button
        type="button"
        size="sm"
        variant="outline"
        className="rounded-full"
        onClick={() => onAdvance(appointment, nextStatus)}
      >
        {getVisitActionLabel(appointment.status)}
      </Button>
    );
  }
  return null;
}

export function UpcomingAppointmentsTable({
  appointments,
  loading,
  onConfirm,
  onAdvance,
  onComplete,
}: UpcomingAppointmentsTableProps) {
  const showActions = Boolean(onConfirm || onAdvance || onComplete);

  return (
    <Card className="rounded-2xl border-border/70 shadow-none">
      <CardHeader className="pb-4">
        <CardTitle className="text-base font-semibold">Upcoming</CardTitle>
        <CardDescription>Next visits on the book</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, index) => (
              <Skeleton key={index} className="h-16 w-full rounded-xl" />
            ))}
          </div>
        ) : appointments.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-xl bg-muted/40 px-4 py-10 text-center">
            <CalendarClock className="mb-3 h-8 w-8 text-muted-foreground/70" />
            <p className="text-sm text-muted-foreground">No upcoming appointments</p>
          </div>
        ) : (
          <ul className="divide-y divide-border/70">
            {appointments.map((appointment) => (
              <li key={appointment.id} className="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-700">
                  {getInitials(appointment.customer_name)}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="truncate text-sm font-medium">{appointment.customer_name}</p>
                    <AppointmentStatusBadge status={appointment.status} />
                  </div>
                  <p className="mt-0.5 truncate text-xs text-muted-foreground">
                    {formatShortDate(appointment.appointment_date)} · {formatTime(appointment.start_time)} ·{" "}
                    {appointment.staff_name}
                  </p>
                </div>
                {showActions ? (
                  <PermissionGate permissions={["appointments:write", "appointments:write_own"]} any>
                    <AppointmentAction
                      appointment={appointment}
                      onConfirm={onConfirm}
                      onAdvance={onAdvance}
                      onComplete={onComplete}
                    />
                  </PermissionGate>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
