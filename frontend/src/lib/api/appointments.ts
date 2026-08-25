import { apiClient, apiRequest } from "@/lib/api/client";
import { apiEndpoints } from "@/config/routes";
import { flattenCalendar } from "@/lib/appointments/calendar-utils";
import type { PaginatedData } from "@/types/api";
import type { Appointment } from "@/types/api";
import type {
  AppointmentCalendarParams,
  AppointmentCalendarResponse,
  AppointmentCreateRequest,
  AppointmentListParams,
  AppointmentRescheduleRequest,
  AppointmentStatusRequest,
  AppointmentUpdateRequest,
} from "@/types/appointments";

export async function fetchAppointmentCalendar(
  params: AppointmentCalendarParams,
): Promise<AppointmentCalendarResponse> {
  return apiRequest(() => apiClient.get(apiEndpoints.appointments.calendar, { params }));
}

export async function fetchCalendarAppointments(params: AppointmentCalendarParams) {
  const calendar = await fetchAppointmentCalendar(params);
  return flattenCalendar(calendar);
}

export async function fetchAppointments(
  params: AppointmentListParams = {},
): Promise<PaginatedData<Appointment>> {
  return apiRequest(() => apiClient.get(apiEndpoints.appointments.list, { params }));
}

export async function fetchAppointment(id: string): Promise<Appointment> {
  return apiRequest(() => apiClient.get(apiEndpoints.appointments.detail(id)));
}

export async function createAppointment(payload: AppointmentCreateRequest): Promise<Appointment> {
  return apiRequest(() => apiClient.post(apiEndpoints.appointments.list, payload));
}

export async function updateAppointment(
  id: string,
  payload: AppointmentUpdateRequest,
): Promise<Appointment> {
  return apiRequest(() => apiClient.put(apiEndpoints.appointments.detail(id), payload));
}

export async function cancelAppointment(id: string): Promise<Appointment> {
  return apiRequest(() => apiClient.patch(apiEndpoints.appointments.cancel(id)));
}

export async function changeAppointmentStatus(
  id: string,
  payload: AppointmentStatusRequest,
): Promise<Appointment> {
  return apiRequest(() => apiClient.patch(apiEndpoints.appointments.status(id), payload));
}

export async function rescheduleAppointment(
  id: string,
  payload: AppointmentRescheduleRequest,
): Promise<Appointment> {
  return apiRequest(() => apiClient.patch(apiEndpoints.appointments.reschedule(id), payload));
}

export { fetchUpcomingAppointments, type UpcomingAppointmentsParams } from "./appointments-upcoming";
