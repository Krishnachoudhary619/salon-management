import { Badge } from "@/components/ui/badge";
import { formatStaffStatus } from "@/lib/schemas/staff";
import type { StaffStatus } from "@/types/staff";

const STATUS_VARIANT: Record<
  StaffStatus,
  "default" | "secondary" | "success" | "warning" | "destructive"
> = {
  ACTIVE: "success",
  INACTIVE: "secondary",
  ON_LEAVE: "warning",
};

export function StaffStatusBadge({ status }: { status: StaffStatus }) {
  return <Badge variant={STATUS_VARIANT[status]}>{formatStaffStatus(status)}</Badge>;
}
