"use client";

import { Eye, FileText } from "lucide-react";

import { PaymentMethodBadge } from "@/components/payments/payment-method-badge";
import { PaymentStatusBadge } from "@/components/payments/payment-status-badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCurrency, formatDateTimeLabel, formatShortDate } from "@/lib/format";
import type { Payment } from "@/types/payments";

interface PaymentsTableProps {
  payments: Payment[];
  loading?: boolean;
  onView: (payment: Payment) => void;
  onPreviewInvoice?: (payment: Payment) => void;
}

export function PaymentsTable({ payments, loading, onView, onPreviewInvoice }: PaymentsTableProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <Skeleton key={index} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (payments.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border py-12 text-center">
        <p className="text-sm font-medium">No payments found</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Record a payment against a completed appointment to get started.
        </p>
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Date</TableHead>
          <TableHead>Amount</TableHead>
          <TableHead>Method</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Appointment</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {payments.map((payment) => (
          <TableRow key={payment.id}>
            <TableCell>
              <div>
                <p className="font-medium">
                  {payment.paid_at ? formatShortDate(payment.paid_at.slice(0, 10)) : "—"}
                </p>
                {payment.paid_at ? (
                  <p className="text-xs text-muted-foreground">{formatDateTimeLabel(payment.paid_at)}</p>
                ) : null}
              </div>
            </TableCell>
            <TableCell className="font-medium">{formatCurrency(payment.amount)}</TableCell>
            <TableCell>
              <PaymentMethodBadge method={payment.payment_method} />
            </TableCell>
            <TableCell>
              <PaymentStatusBadge status={payment.payment_status} />
            </TableCell>
            <TableCell>
              <span className="font-mono text-xs text-muted-foreground">
                {payment.appointment_id.slice(0, 8)}…
              </span>
            </TableCell>
            <TableCell className="text-right">
              <div className="flex justify-end gap-1">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  aria-label="View payment details"
                  onClick={() => onView(payment)}
                >
                  <Eye className="h-4 w-4" />
                </Button>
                {payment.invoice_id && onPreviewInvoice ? (
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    aria-label="Preview invoice"
                    onClick={() => onPreviewInvoice(payment)}
                  >
                    <FileText className="h-4 w-4" />
                  </Button>
                ) : null}
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
