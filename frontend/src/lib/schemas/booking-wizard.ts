import { z } from "zod";

import { toApiTimeValue, toTimeInputValue } from "@/lib/appointments/calendar-utils";
import {
  bookingNewCustomerSchema,
  createEmptyNewCustomer,
  toBookingCustomerPayload,
  type BookingNewCustomerValues,
} from "@/lib/schemas/customer";
import type { AvailabilitySlot } from "@/types/availability";
import type { AppointmentCreateRequest } from "@/types/appointments";
import type { Service } from "@/types/services";

export type CustomerMode = "existing" | "new";

export const BOOKING_STEPS = ["customer", "services", "staff", "date", "time"] as const;

export type BookingStep = (typeof BOOKING_STEPS)[number];

export interface BookingDraft {
  customer_mode: CustomerMode;
  customer_id: string;
  new_customer: BookingNewCustomerValues;
  service_ids: string[];
  staff_id: string;
  appointment_date: string;
  start_time: string;
  notes: string;
}

export const bookingExistingCustomerStepSchema = z.object({
  customer_id: z.string().min(1, "Select a customer"),
});

export const bookingNewCustomerStepSchema = z.object({
  new_customer: bookingNewCustomerSchema,
});

export const bookingServicesStepSchema = z.object({
  service_ids: z.array(z.string()).min(1, "Select at least one service"),
});

export const bookingStaffStepSchema = z.object({
  staff_id: z.string().min(1, "Select a staff member"),
});

export const bookingDateStepSchema = z.object({
  appointment_date: z.string().min(1, "Select a date"),
});

export const bookingTimeStepSchema = z.object({
  start_time: z.string().min(1, "Select an available time slot"),
});

const STEP_SCHEMAS: Record<Exclude<BookingStep, "customer">, z.ZodTypeAny> = {
  services: bookingServicesStepSchema,
  staff: bookingStaffStepSchema,
  date: bookingDateStepSchema,
  time: bookingTimeStepSchema,
};

export function createEmptyBookingDraft(defaults?: Partial<BookingDraft>): BookingDraft {
  return {
    customer_mode: defaults?.customer_mode ?? "existing",
    customer_id: defaults?.customer_id ?? "",
    new_customer: defaults?.new_customer ?? createEmptyNewCustomer(),
    service_ids: defaults?.service_ids ?? [],
    staff_id: defaults?.staff_id ?? "",
    appointment_date: defaults?.appointment_date ?? "",
    start_time: defaults?.start_time ?? "",
    notes: defaults?.notes ?? "",
  };
}

export function getBookingStepIndex(step: BookingStep) {
  return BOOKING_STEPS.indexOf(step);
}

export function getNextBookingStep(step: BookingStep): BookingStep | null {
  const index = getBookingStepIndex(step);
  return BOOKING_STEPS[index + 1] ?? null;
}

export function getPreviousBookingStep(step: BookingStep): BookingStep | null {
  const index = getBookingStepIndex(step);
  return index > 0 ? BOOKING_STEPS[index - 1]! : null;
}

export function validateBookingStep(step: BookingStep, draft: BookingDraft) {
  if (step === "customer") {
    if (draft.customer_mode === "new") {
      return bookingNewCustomerStepSchema.safeParse({ new_customer: draft.new_customer });
    }
    return bookingExistingCustomerStepSchema.safeParse({ customer_id: draft.customer_id });
  }

  const schema = STEP_SCHEMAS[step];
  return schema.safeParse(draft);
}

export function toBookingAppointmentCreatePayload(draft: BookingDraft): AppointmentCreateRequest {
  const base = {
    staff_id: draft.staff_id,
    appointment_date: draft.appointment_date,
    start_time: toApiTimeValue(draft.start_time),
    service_ids: draft.service_ids,
    notes: draft.notes?.trim() || null,
  };

  if (draft.customer_mode === "new") {
    return {
      ...base,
      customer: toBookingCustomerPayload(draft.new_customer),
    };
  }

  return {
    ...base,
    customer_id: draft.customer_id,
  };
}

export function getTotalServiceDuration(serviceIds: string[], services: Service[]) {
  return serviceIds.reduce((total, serviceId) => {
    const service = services.find((item) => item.id === serviceId);
    return total + (service?.duration_minutes ?? 0);
  }, 0);
}

export function slotStartMatches(startTime: string, slot: AvailabilitySlot) {
  return toTimeInputValue(slot.start_time) === toTimeInputValue(startTime);
}

export function isTimeSlotAvailable(startTime: string, slots: AvailabilitySlot[]) {
  if (!startTime) {
    return false;
  }
  return slots.some((slot) => slotStartMatches(startTime, slot));
}

export function getTodayIsoDate() {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0");
  const day = String(today.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}
