import { z } from "zod";

import { toApiTimeValue, toTimeInputValue } from "@/lib/appointments/calendar-utils";
import type { Appointment } from "@/types/api";
import type {
  AppointmentCreateRequest,
  AppointmentRescheduleRequest,
  AppointmentUpdateRequest,
} from "@/types/appointments";

export const appointmentFormSchema = z.object({
  customer_id: z.string().min(1, "Customer is required"),
  staff_id: z.string().min(1, "Staff member is required"),
  appointment_date: z.string().min(1, "Date is required"),
  start_time: z.string().min(1, "Start time is required"),
  service_ids: z.array(z.string()).min(1, "Select at least one service"),
  notes: z.string().max(5000, "Notes are too long").optional(),
});

export const appointmentEditSchema = z.object({
  customer_id: z.string().min(1, "Customer is required"),
  staff_id: z.string().min(1, "Staff member is required"),
  service_ids: z.array(z.string()).min(1, "Select at least one service"),
  notes: z.string().max(5000, "Notes are too long").optional(),
});

export const rescheduleFormSchema = z.object({
  appointment_date: z.string().min(1, "Date is required"),
  start_time: z.string().min(1, "Start time is required"),
  staff_id: z.string().optional(),
});

export type AppointmentFormValues = z.infer<typeof appointmentFormSchema>;
export type AppointmentEditValues = z.infer<typeof appointmentEditSchema>;
export type RescheduleFormValues = z.infer<typeof rescheduleFormSchema>;

export function toAppointmentFormValues(
  appointment?: Appointment,
  defaults?: Partial<AppointmentFormValues>,
): AppointmentFormValues {
  if (appointment) {
    return {
      customer_id: appointment.customer_id,
      staff_id: appointment.staff_id,
      appointment_date: appointment.appointment_date,
      start_time: toTimeInputValue(appointment.start_time),
      service_ids: appointment.services.map((service) => service.service_id),
      notes: appointment.notes ?? "",
    };
  }

  return {
    customer_id: defaults?.customer_id ?? "",
    staff_id: defaults?.staff_id ?? "",
    appointment_date: defaults?.appointment_date ?? "",
    start_time: defaults?.start_time ?? "09:00",
    service_ids: defaults?.service_ids ?? [],
    notes: defaults?.notes ?? "",
  };
}

export function toAppointmentEditValues(appointment: Appointment): AppointmentEditValues {
  return {
    customer_id: appointment.customer_id,
    staff_id: appointment.staff_id,
    service_ids: appointment.services.map((service) => service.service_id),
    notes: appointment.notes ?? "",
  };
}

export function toRescheduleFormValues(appointment: Appointment): RescheduleFormValues {
  return {
    appointment_date: appointment.appointment_date,
    start_time: toTimeInputValue(appointment.start_time),
    staff_id: appointment.staff_id,
  };
}

export function toAppointmentCreatePayload(values: AppointmentFormValues): AppointmentCreateRequest {
  return {
    customer_id: values.customer_id,
    staff_id: values.staff_id,
    appointment_date: values.appointment_date,
    start_time: toApiTimeValue(values.start_time),
    service_ids: values.service_ids,
    notes: values.notes?.trim() || null,
  };
}

export function toAppointmentUpdatePayload(values: AppointmentEditValues): AppointmentUpdateRequest {
  return {
    customer_id: values.customer_id,
    staff_id: values.staff_id,
    service_ids: values.service_ids,
    notes: values.notes?.trim() || null,
  };
}

export function toReschedulePayload(values: RescheduleFormValues): AppointmentRescheduleRequest {
  return {
    appointment_date: values.appointment_date,
    start_time: toApiTimeValue(values.start_time),
    staff_id: values.staff_id || undefined,
  };
}
