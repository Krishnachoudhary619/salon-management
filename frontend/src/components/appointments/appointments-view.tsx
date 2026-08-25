"use client";

import { useMemo, useState } from "react";
import { CalendarDays, Clock3, Plus } from "lucide-react";
import type { DateClickInfo, EventDropInfo } from "@fullcalendar/react";

import { PermissionGate } from "@/components/auth/permission-gate";
import { AppointmentCalendar } from "@/components/appointments/appointment-calendar";
import { AppointmentDetailModal } from "@/components/appointments/appointment-detail-modal";
import { AppointmentFormModal } from "@/components/appointments/appointment-form-modal";
import { BookingWizardModal } from "@/components/appointments/booking-wizard-modal";
import { CancelAppointmentDialog } from "@/components/appointments/cancel-appointment-dialog";
import { CompleteAppointmentDialog } from "@/components/appointments/complete-appointment-dialog";
import { ConfirmAppointmentDialog } from "@/components/appointments/confirm-appointment-dialog";
import { PaymentFormModal } from "@/components/payments/payment-form-modal";
import { PendingAppointmentsPanel } from "@/components/appointments/pending-appointments-panel";
import { RescheduleModal } from "@/components/appointments/reschedule-modal";
import { StatusLegend } from "@/components/appointments/status-legend";
import { ErrorDisplay } from "@/components/feedback/error-display";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAppointmentCalendar, useAppointmentMutations } from "@/hooks/use-appointments";
import { useCustomers } from "@/hooks/use-customers";
import { usePermissions } from "@/hooks/use-permissions";
import { useServices } from "@/hooks/use-services";
import { usePaymentMutations } from "@/hooks/use-payments";
import { useStaff } from "@/hooks/use-staff";
import { toApiTimeValue, toIsoDate } from "@/lib/appointments/calendar-utils";
import { canReschedule, getVisitActionLabel } from "@/lib/appointments/status-colors";
import type { BookingDraft } from "@/lib/schemas/booking-wizard";
import { toAppointmentUpdatePayload, toReschedulePayload } from "@/lib/schemas/appointment";
import { toPaymentCreatePayload } from "@/lib/schemas/payment";
import { toast } from "@/lib/toast";
import { cn } from "@/lib/utils";
import type { Appointment, AppointmentStatus } from "@/types/api";
import type { AppointmentCalendarParams } from "@/types/appointments";

type AppointmentsViewMode = "calendar" | "pending";

function getInitialRange(): AppointmentCalendarParams {
  const today = new Date();
  const start = new Date(today);
  start.setDate(today.getDate() - today.getDay());
  const end = new Date(start);
  end.setDate(start.getDate() + 6);
  return {
    start_date: toIsoDate(start),
    end_date: toIsoDate(end),
  };
}

export function AppointmentsView() {
  const { canAny } = usePermissions();
  const canWrite = canAny(["appointments:write", "appointments:write_own"]);
  const canFilterStaff = canAny(["appointments:read"]);

  const [viewMode, setViewMode] = useState<AppointmentsViewMode>("calendar");
  const [calendarParams, setCalendarParams] = useState<AppointmentCalendarParams>(getInitialRange);
  const [staffFilter, setStaffFilter] = useState<string>("");

  const queryParams = useMemo(
    () => ({
      ...calendarParams,
      staff_id: staffFilter || undefined,
    }),
    [calendarParams, staffFilter],
  );

  const calendarQuery = useAppointmentCalendar(queryParams);
  const customersQuery = useCustomers({ page: 1, limit: 100, sort_by: "name", sort_order: "asc" });
  const staffQuery = useStaff({ page: 1, limit: 100, sort_by: "name", sort_order: "asc", status: "ACTIVE" });
  const servicesQuery = useServices({
    page: 1,
    limit: 100,
    sort_by: "name",
    sort_order: "asc",
    is_active: true,
  });

  const {
    createAppointment,
    updateAppointment,
    cancelAppointment,
    rescheduleAppointment,
    changeAppointmentStatus,
    isCreating,
    isUpdating,
    isCancelling,
    isRescheduling,
    isChangingStatus,
  } = useAppointmentMutations();
  const { createPayment, isCreating: isRecordingPayment } = usePaymentMutations();
  const canRecordPayment = canAny(["payments:write"]);

  const [bookingOpen, setBookingOpen] = useState(false);
  const [bookingDefaults, setBookingDefaults] = useState<Partial<BookingDraft>>();
  const [editOpen, setEditOpen] = useState(false);
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | undefined>();

  const [detailOpen, setDetailOpen] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [completeOpen, setCompleteOpen] = useState(false);
  const [paymentOpen, setPaymentOpen] = useState(false);
  const [rescheduleOpen, setRescheduleOpen] = useState(false);
  const [cancelOpen, setCancelOpen] = useState(false);

  const customers = customersQuery.data?.items ?? [];
  const staff = staffQuery.data?.items ?? [];
  const services = servicesQuery.data?.items ?? [];

  const openBooking = (defaults?: Partial<BookingDraft>) => {
    setBookingDefaults(defaults);
    setBookingOpen(true);
  };

  const openEdit = (appointment: Appointment) => {
    setSelectedAppointment(appointment);
    setDetailOpen(false);
    setEditOpen(true);
  };

  const openDetail = (appointment: Appointment) => {
    setSelectedAppointment(appointment);
    setDetailOpen(true);
  };

  const handleDateClick = (info: DateClickInfo) => {
    if (!canWrite) {
      return;
    }

    const date = info.dateStr.slice(0, 10);
    const time = info.dateStr.includes("T") ? info.dateStr.slice(11, 16) : undefined;

    openBooking({
      appointment_date: date,
      start_time: time,
      staff_id: staffFilter || undefined,
    });
  };

  const handleEventDrop = async (appointment: Appointment, info: EventDropInfo) => {
    if (!canWrite || !canReschedule(appointment.status)) {
      info.revert();
      return;
    }

    const start = info.event.start;
    if (!start) {
      info.revert();
      return;
    }

    try {
      await rescheduleAppointment({
        id: appointment.id,
        payload: {
          appointment_date: toIsoDate(start),
          start_time: toApiTimeValue(
            `${String(start.getHours()).padStart(2, "0")}:${String(start.getMinutes()).padStart(2, "0")}`,
          ),
        },
      });
      toast.success("Appointment rescheduled");
    } catch (error) {
      toast.fromError(error, "Unable to reschedule appointment");
      throw error;
    }
  };

  if (viewMode === "calendar" && calendarQuery.isError) {
    return (
      <ErrorDisplay
        error={calendarQuery.error}
        title="Unable to load appointments"
        onRetry={() => calendarQuery.refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Appointments</h1>
          <p className="text-sm text-muted-foreground">
            Calendar for the week, or a searchable queue of pending website bookings.
          </p>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="inline-flex rounded-full border border-border bg-card p-1">
            <button
              type="button"
              onClick={() => setViewMode("calendar")}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
                viewMode === "calendar" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground",
              )}
            >
              <CalendarDays className="h-4 w-4" />
              Calendar
            </button>
            <button
              type="button"
              onClick={() => setViewMode("pending")}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
                viewMode === "pending" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground",
              )}
            >
              <Clock3 className="h-4 w-4" />
              Pending
            </button>
          </div>
          <PermissionGate permissions={["appointments:write", "appointments:write_own"]} any>
            <Button type="button" onClick={() => openBooking({ staff_id: staffFilter || undefined })}>
              <Plus className="h-4 w-4" />
              Book appointment
            </Button>
          </PermissionGate>
        </div>
      </div>

      {viewMode === "pending" ? (
        <div className="space-y-4">
          {canFilterStaff ? (
            <select
              value={staffFilter}
              onChange={(event) => setStaffFilter(event.target.value)}
              className="h-10 rounded-md border border-input bg-background px-3 text-sm lg:min-w-56"
            >
              <option value="">All staff</option>
              {staff.map((member) => (
                <option key={member.id} value={member.id}>
                  {member.name}
                </option>
              ))}
            </select>
          ) : null}
          <PendingAppointmentsPanel
            staffId={staffFilter || undefined}
            onSelect={openDetail}
            onConfirm={(appointment) => {
              setSelectedAppointment(appointment);
              setConfirmOpen(true);
            }}
          />
        </div>
      ) : (
      <Card>
        <CardHeader className="space-y-4">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <CardTitle>Calendar</CardTitle>
            {canFilterStaff ? (
              <select
                value={staffFilter}
                onChange={(event) => setStaffFilter(event.target.value)}
                className="h-10 rounded-md border border-input bg-background px-3 text-sm lg:min-w-56"
              >
                <option value="">All staff</option>
                {staff.map((member) => (
                  <option key={member.id} value={member.id}>
                    {member.name}
                  </option>
                ))}
              </select>
            ) : null}
          </div>
          <StatusLegend />
        </CardHeader>
        <CardContent>
          <AppointmentCalendar
            appointments={calendarQuery.data ?? []}
            loading={calendarQuery.isFetching}
            editable={canWrite}
            onRangeChange={(range) => setCalendarParams((current) => ({ ...current, ...range }))}
            onDateClick={handleDateClick}
            onEventClick={openDetail}
            onEventDrop={canWrite ? handleEventDrop : undefined}
          />
        </CardContent>
      </Card>
      )}

      <BookingWizardModal
        open={bookingOpen}
        customers={customers}
        staff={staff}
        services={services}
        defaults={bookingDefaults}
        loading={isCreating}
        onOpenChange={setBookingOpen}
        onSubmit={async (payload) => {
          await createAppointment(payload);
          toast.success("Appointment booked");
        }}
      />

      <AppointmentFormModal
        open={editOpen}
        mode="edit"
        appointment={selectedAppointment}
        customers={customers}
        staff={staff}
        services={services}
        loading={isUpdating}
        onOpenChange={setEditOpen}
        onSubmit={async (values) => {
          if (selectedAppointment) {
            await updateAppointment({
              id: selectedAppointment.id,
              payload: toAppointmentUpdatePayload(values),
            });
            toast.success("Appointment updated");
          }
        }}
      />

      <AppointmentDetailModal
        open={detailOpen}
        appointment={selectedAppointment}
        loading={isUpdating || isCancelling || isRescheduling || isChangingStatus}
        onOpenChange={setDetailOpen}
        onEdit={openEdit}
        onConfirm={(appointment) => {
          setSelectedAppointment(appointment);
          setDetailOpen(false);
          setConfirmOpen(true);
        }}
        onAdvance={async (appointment, status) => {
          try {
            const updated = await changeAppointmentStatus({
              id: appointment.id,
              payload: { status },
            });
            setSelectedAppointment(updated);
            toast.success(getVisitActionLabel(appointment.status) ?? "Appointment updated");
          } catch (error) {
            toast.fromError(error, "Unable to update appointment");
          }
        }}
        onComplete={(appointment) => {
          setSelectedAppointment(appointment);
          setDetailOpen(false);
          setCompleteOpen(true);
        }}
        onReschedule={(appointment) => {
          setSelectedAppointment(appointment);
          setDetailOpen(false);
          setRescheduleOpen(true);
        }}
        onCancel={(appointment) => {
          setSelectedAppointment(appointment);
          setDetailOpen(false);
          setCancelOpen(true);
        }}
      />

      <CompleteAppointmentDialog
        open={completeOpen}
        appointment={selectedAppointment}
        loading={isChangingStatus}
        onOpenChange={setCompleteOpen}
        onConfirm={async () => {
          if (!selectedAppointment) {
            return;
          }
          try {
            const updated = await changeAppointmentStatus({
              id: selectedAppointment.id,
              payload: { status: "COMPLETED" },
            });
            setSelectedAppointment(updated);
            toast.success("Visit completed. Invoice created.");
            if (canRecordPayment) {
              setPaymentOpen(true);
            }
          } catch (error) {
            toast.fromError(error, "Unable to complete appointment");
            throw error;
          }
        }}
      />

      <PaymentFormModal
        open={paymentOpen}
        appointments={selectedAppointment ? [selectedAppointment] : []}
        defaultAppointmentId={selectedAppointment?.id}
        loading={isRecordingPayment}
        onOpenChange={setPaymentOpen}
        onSubmit={async (values) => {
          await createPayment(toPaymentCreatePayload(values));
          toast.success("Payment recorded");
        }}
      />

      <ConfirmAppointmentDialog
        open={confirmOpen}
        appointment={selectedAppointment}
        staff={staff}
        loading={isChangingStatus}
        onOpenChange={setConfirmOpen}
        onConfirm={async (staffId) => {
          if (!selectedAppointment) {
            return;
          }
          try {
            await changeAppointmentStatus({
              id: selectedAppointment.id,
              payload: { status: "CONFIRMED", staff_id: staffId },
            });
            toast.success("Appointment confirmed");
          } catch (error) {
            toast.fromError(error, "Unable to confirm appointment");
            throw error;
          }
        }}
      />

      <RescheduleModal
        open={rescheduleOpen}
        appointment={selectedAppointment}
        staff={staff}
        loading={isRescheduling}
        onOpenChange={setRescheduleOpen}
        onSubmit={async (values) => {
          if (!selectedAppointment) {
            return;
          }
          await rescheduleAppointment({
            id: selectedAppointment.id,
            payload: toReschedulePayload(values),
          });
          toast.success("Appointment rescheduled");
        }}
      />

      <CancelAppointmentDialog
        open={cancelOpen}
        customerName={selectedAppointment?.customer_name}
        loading={isCancelling}
        onOpenChange={setCancelOpen}
        onConfirm={async () => {
          if (!selectedAppointment) {
            return;
          }
          await cancelAppointment(selectedAppointment.id);
          toast.success("Appointment cancelled");
        }}
      />
    </div>
  );
}
