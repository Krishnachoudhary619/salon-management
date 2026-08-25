export interface Customer {
  id: string;
  name: string;
  phone: string;
  email: string | null;
  notes: string | null;
  visit_count: number;
  total_spent: string;
  last_visit: string | null;
  created_at: string;
  updated_at: string;
}

export interface CustomerListParams {
  page?: number;
  limit?: number;
  search?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  phone?: string;
}

export interface CustomerCreateRequest {
  name: string;
  phone: string;
  email?: string | null;
  notes?: string | null;
}
