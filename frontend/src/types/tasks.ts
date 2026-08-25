export type TaskStatus = "PENDING" | "IN_PROGRESS" | "COMPLETED";

export interface Task {
  id: string;
  assigned_staff_id: string;
  assigned_staff_name: string;
  title: string;
  description: string | null;
  status: TaskStatus;
  due_date: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskCreateRequest {
  assigned_staff_id: string;
  title: string;
  description?: string | null;
  due_date?: string | null;
}

export interface TaskUpdateRequest {
  assigned_staff_id?: string;
  title?: string;
  description?: string | null;
  status?: TaskStatus;
  due_date?: string | null;
}

export interface TaskListParams {
  page?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  assigned_staff_id?: string;
  status?: TaskStatus;
  search?: string;
}
