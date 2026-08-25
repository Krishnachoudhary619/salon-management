import type { TaskStatus } from "@/types/tasks";
import { Badge } from "@/components/ui/badge";
import { formatStatusLabel } from "@/lib/format";

const STATUS_VARIANT: Record<
  TaskStatus,
  "default" | "secondary" | "success" | "warning" | "destructive"
> = {
  PENDING: "secondary",
  IN_PROGRESS: "warning",
  COMPLETED: "success",
};

export function TaskStatusBadge({ status }: { status: TaskStatus }) {
  return <Badge variant={STATUS_VARIANT[status]}>{formatStatusLabel(status)}</Badge>;
}
