export interface InvoiceLineItem {
  service_id: string;
  service_name: string;
  duration_minutes: number;
  price: string;
}

export interface Invoice {
  id: string;
  appointment_id: string;
  invoice_number: string;
  subtotal: string;
  tax: string;
  total: string;
  paid_amount: string;
  is_paid: boolean;
  line_items: InvoiceLineItem[];
  created_at: string;
  updated_at: string;
}

export interface InvoiceListParams {
  page?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  appointment_id?: string;
}
