import { z } from "zod";

import type { TaskCreateRequest, TaskUpdateRequest } from "@/types/tasks";

export const taskFormSchema = z.object({
  assigned_staff_id: z.string().min(1, "Select a staff member"),
  title: z.string().min(1, "Title is required").max(200, "Title is too long"),
  description: z.string().max(5000, "Description is too long").optional(),
  due_date: z.string().optional(),
});

export type TaskFormValues = z.infer<typeof taskFormSchema>;

export function toTaskCreatePayload(values: TaskFormValues): TaskCreateRequest {
  return {
    assigned_staff_id: values.assigned_staff_id,
    title: values.title.trim(),
    description: values.description?.trim() || null,
    due_date: values.due_date || null,
  };
}

export function toTaskStatusUpdatePayload(status: TaskUpdateRequest["status"]): TaskUpdateRequest {
  return { status };
}
