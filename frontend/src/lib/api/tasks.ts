import { apiClient, apiRequest } from "@/lib/api/client";
import { apiEndpoints } from "@/config/routes";
import type { PaginatedData } from "@/types/api";
import type { Task, TaskCreateRequest, TaskListParams, TaskUpdateRequest } from "@/types/tasks";

export async function fetchTasks(params: TaskListParams = {}): Promise<PaginatedData<Task>> {
  return apiRequest(() => apiClient.get(apiEndpoints.tasks.list, { params }));
}

export async function fetchTask(id: string): Promise<Task> {
  return apiRequest(() => apiClient.get(apiEndpoints.tasks.detail(id)));
}

export async function createTask(payload: TaskCreateRequest): Promise<Task> {
  return apiRequest(() => apiClient.post(apiEndpoints.tasks.list, payload));
}

export async function updateTask(id: string, payload: TaskUpdateRequest): Promise<Task> {
  return apiRequest(() => apiClient.put(apiEndpoints.tasks.detail(id), payload));
}
