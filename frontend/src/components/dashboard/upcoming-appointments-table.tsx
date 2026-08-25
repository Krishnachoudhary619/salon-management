"use client";

import { PermissionGate } from "@/components/auth/permission-gate";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { AppointmentStatusBadge } from "@/components/dashboard/appointment-status-badge";
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

export function UpcomingAppointmentsTable({
  appointments,
  loading,
  onConfirm,
  onAdvance,
  onComplete,
}: UpcomingAppointmentsTableProps) {
  const showActions = Boolean(onConfirm || onAdvance || onComplete);
  return (
    <Card>
      <CardHeader>
        <CardTitle>Upcoming Appointments</CardTitle>
        <CardDescription>Next scheduled visits</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, index) => (
              <Skeleton key={index} className="h-10 w-full" />
            ))}
          </div>
        ) : appointments.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">No upcoming appointments</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Customer</TableHead>
                <TableHead>Staff</TableHead>
                <TableHead>When</TableHead>
                <TableHead>Status</TableHead>
                {showActions ? <TableHead className="text-right">Action</TableHead> : null}
              </TableRow>
            </TableHeader>
            <TableBody>
              {appointments.map((appointment) => (
                <TableRow key={appointment.id}>
                  <TableCell className="font-medium">{appointment.customer_name}</TableCell>
                  <TableCell>{appointment.staff_name}</TableCell>
                  <TableCell>
                    {formatShortDate(appointment.appointment_date)} · {formatTime(appointment.start_time)}
                  </TableCell>
                  <TableCell>
                    <AppointmentStatusBadge status={appointment.status} />
                  </TableCell>
                  {showActions ? (
                    <TableCell className="text-right">
                      <PermissionGate permissions={["appointments:write", "appointments:write_own"]} any>
                        {canConfirm(appointment.status) && onConfirm ? (
                          <Button type="button" size="sm" onClick={() => onConfirm(appointment)}>
                            Confirm
                          </Button>
                        ) : null}
                        {canComplete(appointment.status) && onComplete ? (
                          <Button type="button" size="sm" onClick={() => onComplete(appointment)}>
                            Complete
                          </Button>
                        ) : null}
                        {!canConfirm(appointment.status) &&
                        !canComplete(appointment.status) &&
                        onAdvance &&
                        getNextVisitStatus(appointment.status) ? (
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            onClick={() => onAdvance(appointment, getNextVisitStatus(appointment.status)!)}
                          >
                            {getVisitActionLabel(appointment.status)}
                          </Button>
                        ) : null}
                      </PermissionGate>
                    </TableCell>
                  ) : null}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
