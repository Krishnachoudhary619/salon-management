import type { PaymentMethod } from "@/types/payments";
import { Badge } from "@/components/ui/badge";

const METHOD_LABELS: Record<PaymentMethod, string> = {
  CASH: "Cash",
  CARD: "Card",
  UPI: "UPI",
};

const METHOD_VARIANT: Record<PaymentMethod, "default" | "secondary" | "outline"> = {
  CASH: "secondary",
  CARD: "default",
  UPI: "outline",
};

export function PaymentMethodBadge({ method }: { method: PaymentMethod }) {
  return <Badge variant={METHOD_VARIANT[method]}>{METHOD_LABELS[method]}</Badge>;
}
