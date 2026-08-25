"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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
import { formatShortDate, formatTime } from "@/lib/format";
import type { Appointment } from "@/types/api";

interface UpcomingAppointmentsTableProps {
  appointments: Appointment[];
  loading?: boolean;
}

export function UpcomingAppointmentsTable({ appointments, loading }: UpcomingAppointmentsTableProps) {
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
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
