import type { TaskStatus } from "@/types/tasks";

const NEXT_STATUS: Record<TaskStatus, TaskStatus | null> = {
  PENDING: "IN_PROGRESS",
  IN_PROGRESS: "COMPLETED",
  COMPLETED: null,
};

const STATUS_ACTION_LABEL: Record<TaskStatus, string> = {
  PENDING: "Start",
  IN_PROGRESS: "Complete",
  COMPLETED: "Completed",
};

export function getNextTaskStatus(status: TaskStatus): TaskStatus | null {
  return NEXT_STATUS[status];
}

export function getStatusActionLabel(status: TaskStatus): string {
  const next = getNextTaskStatus(status);
  return next ? STATUS_ACTION_LABEL[status] : STATUS_ACTION_LABEL.COMPLETED;
}

export function canAdvanceTaskStatus(status: TaskStatus) {
  return getNextTaskStatus(status) !== null;
}
