import { apiClient, apiRequest } from "@/lib/api/client";
import { apiEndpoints } from "@/config/routes";
import type { Appointment } from "@/types/api";
import type { AvailabilityParams, AvailabilityResponse } from "@/types/availability";

export interface PublicService {
  id: string;
  name: string;
  duration_minutes: number;
  price: string;
  category: string;
}

export interface PublicStaff {
  id: string;
  name: string;
  designation: string;
}

export interface PublicCatalog {
  services: PublicService[];
  staff: PublicStaff[];
}

export interface PublicBookingRequest {
  name: string;
  phone: string;
  staff_id: string;
  service_id: string;
  appointment_date: string;
  start_time: string;
  notes?: string | null;
}

export async function fetchPublicCatalog(): Promise<PublicCatalog> {
  return apiRequest(() => apiClient.get(apiEndpoints.public.catalog));
}

export async function fetchPublicAvailability(params: AvailabilityParams): Promise<AvailabilityResponse> {
  return apiRequest(() =>
    apiClient.get(apiEndpoints.public.availability, {
      params: {
        staff_id: params.staff_id,
        date: params.date,
        duration_minutes: params.duration_minutes,
      },
    }),
  );
}

export async function createPublicBooking(payload: PublicBookingRequest): Promise<Appointment> {
  return apiRequest(() => apiClient.post(apiEndpoints.public.bookings, payload));
}
