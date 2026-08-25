import type { PaymentStatus } from "@/types/payments";
import { Badge } from "@/components/ui/badge";
import { formatStatusLabel } from "@/lib/format";

const STATUS_VARIANT: Record<
  PaymentStatus,
  "default" | "secondary" | "success" | "warning" | "destructive"
> = {
  PENDING: "warning",
  SUCCESS: "success",
  FAILED: "destructive",
  REFUNDED: "secondary",
};

export function PaymentStatusBadge({ status }: { status: PaymentStatus }) {
  return <Badge variant={STATUS_VARIANT[status]}>{formatStatusLabel(status)}</Badge>;
}
