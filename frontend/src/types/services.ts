export interface Service {
  id: string;
  name: string;
  description: string | null;
  category: string;
  duration_minutes: number;
  price: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ServiceCreateRequest {
  name: string;
  description?: string | null;
  category: string;
  duration_minutes: number;
  price: number;
  is_active?: boolean;
}

export interface ServiceUpdateRequest {
  name?: string;
  description?: string | null;
  category?: string;
  duration_minutes?: number;
  price?: number;
  is_active?: boolean;
}

export interface ServiceListParams {
  page?: number;
  limit?: number;
  search?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  is_active?: boolean;
  category?: string;
}
