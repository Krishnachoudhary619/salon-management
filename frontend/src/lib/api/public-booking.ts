import { apiClient, apiRequest } from "@/lib/api/client";
import { apiEndpoints } from "@/config/routes";
import type { Appointment } from "@/types/api";
import type { AvailabilitySlot } from "@/types/availability";

export interface PublicService {
  id: string;
  name: string;
  duration_minutes: number;
  price: string;
  category: string;
}

export interface PublicCatalog {
  services: PublicService[];
}

export interface PublicAvailabilityParams {
  date: string;
  duration_minutes: number;
}

export interface PublicAvailabilityResponse {
  date: string;
  duration_minutes: number;
  slots: AvailabilitySlot[];
}

export interface PublicBookingRequest {
  name: string;
  phone: string;
  service_id: string;
  appointment_date: string;
  start_time: string;
  notes?: string | null;
}

export async function fetchPublicCatalog(): Promise<PublicCatalog> {
  return apiRequest(() => apiClient.get(apiEndpoints.public.catalog));
}

export async function fetchPublicAvailability(
  params: PublicAvailabilityParams,
): Promise<PublicAvailabilityResponse> {
  return apiRequest(() =>
    apiClient.get(apiEndpoints.public.availability, {
      params: {
        date: params.date,
        duration_minutes: params.duration_minutes,
      },
    }),
  );
}

export async function createPublicBooking(payload: PublicBookingRequest): Promise<Appointment> {
  return apiRequest(() => apiClient.post(apiEndpoints.public.bookings, payload));
}
