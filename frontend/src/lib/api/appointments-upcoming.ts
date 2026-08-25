import { apiClient, apiRequest } from "@/lib/api/client";
import { apiEndpoints } from "@/config/routes";
import { toIsoDate } from "@/lib/format";
import type { Appointment, AppointmentStatus, PaginatedData } from "@/types/api";

const TERMINAL_STATUSES: AppointmentStatus[] = ["COMPLETED", "CANCELLED", "NO_SHOW"];

export interface UpcomingAppointmentsParams {
  limit?: number;
  daysAhead?: number;
}

export async function fetchUpcomingAppointments({
  limit = 8,
  daysAhead = 14,
}: UpcomingAppointmentsParams = {}): Promise<Appointment[]> {
  const today = new Date();
  const end = new Date(today);
  end.setDate(end.getDate() + daysAhead);

  const page = await apiRequest<PaginatedData<Appointment>>(() =>
    apiClient.get(apiEndpoints.appointments.list, {
      params: {
        page: 1,
        limit: 50,
        sort_by: "appointment_date",
        sort_order: "asc",
        date_from: toIsoDate(today),
        date_to: toIsoDate(end),
      },
    }),
  );

  return page.items
    .filter((appointment) => !TERMINAL_STATUSES.includes(appointment.status))
    .slice(0, limit);
}
