import { apiClient, apiRequest } from "@/lib/api/client";
import { apiEndpoints } from "@/config/routes";
import type { AvailabilityParams, AvailabilityResponse } from "@/types/availability";

export async function fetchAvailability(params: AvailabilityParams): Promise<AvailabilityResponse> {
  return apiRequest(() =>
    apiClient.get(apiEndpoints.availability.list, {
      params: {
        staff_id: params.staff_id,
        date: params.date,
        duration_minutes: params.duration_minutes,
      },
    }),
  );
}
