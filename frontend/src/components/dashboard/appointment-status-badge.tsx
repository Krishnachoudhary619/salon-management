import type { AppointmentStatus } from "@/types/api";
import { Badge } from "@/components/ui/badge";
import { formatStatusLabel } from "@/lib/format";

const STATUS_VARIANT: Record<
  AppointmentStatus,
  "default" | "secondary" | "success" | "warning" | "destructive"
> = {
  PENDING: "secondary",
  CONFIRMED: "default",
  ARRIVED: "warning",
  IN_PROGRESS: "warning",
  COMPLETED: "success",
  CANCELLED: "destructive",
  NO_SHOW: "destructive",
};

export function AppointmentStatusBadge({ status }: { status: AppointmentStatus }) {
  return <Badge variant={STATUS_VARIANT[status]}>{formatStatusLabel(status)}</Badge>;
}
