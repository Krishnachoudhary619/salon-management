import type { Appointment, AppointmentStatus } from "@/types/api";

export interface CalendarDay {
  date: string;
  appointments: Appointment[];
}

export interface AppointmentCalendarResponse {
  start_date: string;
  end_date: string;
  days: CalendarDay[];
}

export interface AppointmentCalendarParams {
  start_date: string;
  end_date: string;
  staff_id?: string;
}

import type { CustomerCreateRequest } from "@/types/customers";

export interface AppointmentCreateRequest {
  customer_id?: string;
  customer?: CustomerCreateRequest;
  staff_id: string;
  appointment_date: string;
  start_time: string;
  service_ids: string[];
  notes?: string | null;
}

export interface AppointmentUpdateRequest {
  notes?: string | null;
  staff_id?: string;
  customer_id?: string;
  service_ids?: string[];
}

export interface AppointmentRescheduleRequest {
  appointment_date: string;
  start_time: string;
  staff_id?: string;
}

export interface AppointmentStatusRequest {
  status: AppointmentStatus;
  staff_id?: string;
}

export interface AppointmentListParams {
  page?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  staff_id?: string;
  customer_id?: string;
  status?: AppointmentStatus;
  appointment_date?: string;
  date_from?: string;
  date_to?: string;
}

export interface CalendarEventInput {
  id: string;
  title: string;
  start: string;
  end: string;
  backgroundColor: string;
  borderColor: string;
  textColor: string;
  extendedProps: {
    appointment: Appointment;
  };
}

export type { Appointment, AppointmentStatus };
