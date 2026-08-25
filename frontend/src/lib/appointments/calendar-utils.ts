import { APPOINTMENT_STATUS_COLORS } from "@/lib/appointments/status-colors";
import type { Appointment } from "@/types/api";
import type { AppointmentCalendarResponse, CalendarEventInput } from "@/types/appointments";

export function toDateTimeIso(date: string, time: string) {
  const normalized = time.length === 5 ? `${time}:00` : time;
  return `${date}T${normalized}`;
}

export function flattenCalendar(response: AppointmentCalendarResponse) {
  return response.days.flatMap((day) => day.appointments);
}

export function appointmentToEvent(appointment: Appointment): CalendarEventInput {
  const colors = APPOINTMENT_STATUS_COLORS[appointment.status];
  const serviceLabel =
    appointment.services.length > 0
      ? appointment.services.map((service) => service.service_name).join(", ")
      : "Appointment";

  return {
    id: appointment.id,
    title: `${appointment.customer_name} · ${serviceLabel}`,
    start: toDateTimeIso(appointment.appointment_date, appointment.start_time),
    end: toDateTimeIso(appointment.appointment_date, appointment.end_time),
    backgroundColor: colors.bg,
    borderColor: colors.border,
    textColor: colors.text,
    extendedProps: { appointment },
  };
}

export function toIsoDate(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function addDays(date: Date, days: number) {
  const next = new Date(date);
  next.setDate(next.getDate() + days);
  return next;
}

export function getCalendarRange(viewStart: Date, viewEnd: Date) {
  return {
    start_date: toIsoDate(viewStart),
    end_date: toIsoDate(addDays(viewEnd, -1)),
  };
}

export function toTimeInputValue(time: string) {
  return time.slice(0, 5);
}

export function toApiTimeValue(time: string) {
  return time.length === 5 ? `${time}:00` : time;
}
