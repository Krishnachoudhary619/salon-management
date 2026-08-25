export type StaffStatus = "ACTIVE" | "INACTIVE" | "ON_LEAVE";

export interface StaffMember {
  id: string;
  user_id: string;
  name: string;
  email: string | null;
  phone: string;
  designation: string;
  commission_percentage: string;
  joining_date: string;
  status: StaffStatus;
  created_at: string;
  updated_at: string;
}

export interface StaffCreateRequest {
  name: string;
  email: string;
  password: string;
  phone: string;
  designation: string;
  commission_percentage: number;
  joining_date: string;
  status?: StaffStatus;
}

export interface StaffUpdateRequest {
  name?: string;
  phone?: string;
  designation?: string;
  commission_percentage?: number;
  joining_date?: string;
  status?: StaffStatus;
}

export interface StaffListParams {
  page?: number;
  limit?: number;
  search?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  status?: StaffStatus;
}
