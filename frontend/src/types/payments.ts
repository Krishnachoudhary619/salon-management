export type PaymentMethod = "CASH" | "CARD" | "UPI";

export type PaymentStatus = "PENDING" | "SUCCESS" | "FAILED" | "REFUNDED";

export interface Payment {
  id: string;
  appointment_id: string;
  invoice_id: string | null;
  amount: string;
  payment_method: PaymentMethod;
  payment_status: PaymentStatus;
  paid_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaymentCreateRequest {
  appointment_id: string;
  amount: number;
  payment_method: PaymentMethod;
  payment_status?: PaymentStatus;
}

export interface PaymentListParams {
  page?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  appointment_id?: string;
  payment_method?: PaymentMethod;
  status?: PaymentStatus;
}
