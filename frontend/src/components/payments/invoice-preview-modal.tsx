"use client";

import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import { ErrorDisplay } from "@/components/feedback/error-display";
import { LoadingSpinner } from "@/components/feedback/loading-state";
import { useInvoice } from "@/hooks/use-invoices";
import { formatCurrency, formatDateTimeLabel } from "@/lib/format";
import type { Invoice } from "@/types/invoices";

interface InvoicePreviewModalProps {
  open: boolean;
  invoiceId?: string;
  onOpenChange: (open: boolean) => void;
}

function InvoicePreviewContent({ invoice }: { invoice: Invoice }) {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-border pb-4">
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Invoice</p>
          <p className="text-xl font-semibold">{invoice.invoice_number}</p>
        </div>
        <Badge variant={invoice.is_paid ? "success" : "warning"}>
          {invoice.is_paid ? "Paid" : "Outstanding"}
        </Badge>
      </div>

      <div className="rounded-md border border-border">
        <div className="border-b border-border bg-muted/30 px-4 py-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Line items
        </div>
        <ul className="divide-y divide-border">
          {invoice.line_items.map((item) => (
            <li key={item.service_id} className="flex items-center justify-between px-4 py-3 text-sm">
              <div>
                <p className="font-medium">{item.service_name}</p>
                <p className="text-muted-foreground">{item.duration_minutes} min</p>
              </div>
              <span className="font-medium">{formatCurrency(item.price)}</span>
            </li>
          ))}
        </ul>
      </div>

      <dl className="space-y-2 text-sm">
        <div className="flex justify-between">
          <dt className="text-muted-foreground">Subtotal</dt>
          <dd>{formatCurrency(invoice.subtotal)}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-muted-foreground">Tax</dt>
          <dd>{formatCurrency(invoice.tax)}</dd>
        </div>
        <div className="flex justify-between border-t border-border pt-2 text-base font-semibold">
          <dt>Total</dt>
          <dd>{formatCurrency(invoice.total)}</dd>
        </div>
        <div className="flex justify-between text-emerald-700">
          <dt>Paid</dt>
          <dd>{formatCurrency(invoice.paid_amount)}</dd>
        </div>
        {!invoice.is_paid ? (
          <div className="flex justify-between font-medium text-amber-700">
            <dt>Balance due</dt>
            <dd>
              {formatCurrency(
                Math.max(
                  0,
                  Number.parseFloat(invoice.total) - Number.parseFloat(invoice.paid_amount),
                ),
              )}
            </dd>
          </div>
        ) : null}
      </dl>

      <p className="text-xs text-muted-foreground">
        Issued {formatDateTimeLabel(invoice.created_at)} · Appointment {invoice.appointment_id.slice(0, 8)}…
      </p>
    </div>
  );
}

export function InvoicePreviewModal({ open, invoiceId, onOpenChange }: InvoicePreviewModalProps) {
  const invoiceQuery = useInvoice(invoiceId);

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Invoice preview"
      description="Review invoice line items and payment balance."
      className="max-w-lg"
    >
      {invoiceQuery.isLoading ? <LoadingSpinner label="Loading invoice" /> : null}
      {invoiceQuery.isError ? (
        <ErrorDisplay
          error={invoiceQuery.error}
          title="Unable to load invoice"
          onRetry={() => invoiceQuery.refetch()}
        />
      ) : null}
      {invoiceQuery.data ? <InvoicePreviewContent invoice={invoiceQuery.data} /> : null}
    </Dialog>
  );
}
