export interface Tip {
  id: string;
  appointment_id: string;
  staff_id: string;
  staff_name: string;
  amount: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface TipCreateRequest {
  appointment_id: string;
  amount: number;
  notes?: string | null;
}

export interface TipUpdateRequest {
  amount?: number;
  notes?: string | null;
}

export interface TipListParams {
  page?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  staff_id?: string;
  appointment_id?: string;
  search?: string;
}

export interface StaffTipSummary {
  month: string;
  tipTotal: number;
  count: number;
}
