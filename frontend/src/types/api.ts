export type Role = "ADMIN" | "RECEPTIONIST" | "STAFF";

export type Permission =
  | "users:read"
  | "users:write"
  | "staff:read"
  | "staff:write"
  | "staff:delete"
  | "services:read"
  | "services:write"
  | "services:delete"
  | "customers:read"
  | "customers:write"
  | "schedules:read"
  | "schedules:write"
  | "appointments:read"
  | "appointments:read_own"
  | "appointments:write"
  | "appointments:write_own"
  | "payments:read"
  | "payments:write"
  | "invoices:read"
  | "commissions:read"
  | "commissions:read_own"
  | "commissions:config"
  | "tips:read"
  | "tips:read_own"
  | "tips:write"
  | "tasks:read"
  | "tasks:read_own"
  | "tasks:write"
  | "tasks:write_own"
  | "dashboard:read"
  | "reports:read"
  | "performance:read"
  | "performance:read_own";

export interface ApiErrorItem {
  field: string | null;
  message: string;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T | null;
}

export interface ApiErrorResponse {
  success: false;
  message: string;
  errors: ApiErrorItem[];
}

export interface PaginatedData<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}

export type AppointmentStatus =
  | "PENDING"
  | "CONFIRMED"
  | "ARRIVED"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "CANCELLED"
  | "NO_SHOW";

export interface AppointmentLine {
  id: string;
  service_id: string;
  service_name: string;
  duration_minutes: number;
  price: string;
}

export interface Appointment {
  id: string;
  customer_id: string;
  customer_name: string;
  customer_phone: string;
  staff_id: string;
  staff_name: string;
  appointment_date: string;
  start_time: string;
  end_time: string;
  status: AppointmentStatus;
  notes: string | null;
  duration_minutes: number;
  services: AppointmentLine[];
  cancelled_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  is_active: boolean;
  roles: Role[];
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  user: AuthUser;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}
