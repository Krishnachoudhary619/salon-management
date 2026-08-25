"use client";

import { FileText } from "lucide-react";

import { PaymentMethodBadge } from "@/components/payments/payment-method-badge";
import { PaymentStatusBadge } from "@/components/payments/payment-status-badge";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { formatCurrency, formatDateTimeLabel } from "@/lib/format";
import type { Payment } from "@/types/payments";

interface PaymentDetailModalProps {
  open: boolean;
  payment?: Payment;
  onOpenChange: (open: boolean) => void;
  onPreviewInvoice?: (payment: Payment) => void;
}

export function PaymentDetailModal({
  open,
  payment,
  onOpenChange,
  onPreviewInvoice,
}: PaymentDetailModalProps) {
  if (!payment) {
    return null;
  }

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Payment details"
      description={`Payment ${payment.id.slice(0, 8)}…`}
      className="max-w-lg"
    >
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <PaymentMethodBadge method={payment.payment_method} />
          <PaymentStatusBadge status={payment.payment_status} />
        </div>

        <dl className="grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-muted-foreground">Amount</dt>
            <dd className="text-lg font-semibold">{formatCurrency(payment.amount)}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Paid at</dt>
            <dd className="font-medium">
              {payment.paid_at ? formatDateTimeLabel(payment.paid_at) : "—"}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Appointment</dt>
            <dd className="font-mono text-xs">{payment.appointment_id}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Invoice</dt>
            <dd className="font-mono text-xs">{payment.invoice_id ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Recorded</dt>
            <dd className="font-medium">{formatDateTimeLabel(payment.created_at)}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Updated</dt>
            <dd className="font-medium">{formatDateTimeLabel(payment.updated_at)}</dd>
          </div>
        </dl>

        {payment.invoice_id && onPreviewInvoice ? (
          <div className="flex justify-end border-t border-border pt-4">
            <Button type="button" variant="outline" onClick={() => onPreviewInvoice(payment)}>
              <FileText className="h-4 w-4" />
              Preview invoice
            </Button>
          </div>
        ) : null}
      </div>
    </Dialog>
  );
}
