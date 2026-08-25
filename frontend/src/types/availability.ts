export interface AvailabilitySlot {
  start_time: string;
  end_time: string;
}

export interface AvailabilityResponse {
  staff_id: string;
  date: string;
  duration_minutes: number;
  slots: AvailabilitySlot[];
}

export interface AvailabilityParams {
  staff_id: string;
  date: string;
  duration_minutes: number;
}
