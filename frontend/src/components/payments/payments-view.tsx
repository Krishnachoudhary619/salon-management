"use client";

import { useMemo, useState } from "react";
import { Plus } from "lucide-react";

import { PermissionGate } from "@/components/auth/permission-gate";
import { InvoicePreviewModal } from "@/components/payments/invoice-preview-modal";
import { PaymentDetailModal } from "@/components/payments/payment-detail-modal";
import { PaymentFormModal } from "@/components/payments/payment-form-modal";
import { PaymentsTable } from "@/components/payments/payments-table";
import { ErrorDisplay } from "@/components/feedback/error-display";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAppointments } from "@/hooks/use-appointments";
import { usePaymentMutations, usePayments } from "@/hooks/use-payments";
import { toPaymentCreatePayload } from "@/lib/schemas/payment";
import { toast } from "@/lib/toast";
import type { Payment, PaymentMethod, PaymentStatus } from "@/types/payments";

type MethodFilter = PaymentMethod | "all";
type StatusFilter = PaymentStatus | "all";

export function PaymentsView() {
  const [page, setPage] = useState(1);
  const [methodFilter, setMethodFilter] = useState<MethodFilter>("all");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

  const listParams = useMemo(
    () => ({
      page,
      limit: 10,
      sort_by: "created_at",
      sort_order: "desc" as const,
      payment_method: methodFilter === "all" ? undefined : methodFilter,
      status: statusFilter === "all" ? undefined : statusFilter,
    }),
    [page, methodFilter, statusFilter],
  );

  const paymentsQuery = usePayments(listParams);
  const completedAppointmentsQuery = useAppointments({
    page: 1,
    limit: 100,
    status: "COMPLETED",
    sort_by: "appointment_date",
    sort_order: "desc",
  });

  const { createPayment, isCreating } = usePaymentMutations();

  const [formOpen, setFormOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const [invoiceOpen, setInvoiceOpen] = useState(false);
  const [selectedPayment, setSelectedPayment] = useState<Payment | undefined>();
  const [previewInvoiceId, setPreviewInvoiceId] = useState<string | undefined>();

  const openDetail = (payment: Payment) => {
    setSelectedPayment(payment);
    setDetailOpen(true);
  };

  const openInvoicePreview = (payment: Payment) => {
    if (!payment.invoice_id) {
      return;
    }
    setPreviewInvoiceId(payment.invoice_id);
    setInvoiceOpen(true);
  };

  if (paymentsQuery.isError) {
    return (
      <ErrorDisplay
        error={paymentsQuery.error}
        title="Unable to load payments"
        onRetry={() => paymentsQuery.refetch()}
      />
    );
  }

  const totalPages = paymentsQuery.data
    ? Math.ceil(paymentsQuery.data.total / paymentsQuery.data.limit)
    : 1;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Payments</h1>
          <p className="text-sm text-muted-foreground">
            Payment history, recording, and invoice preview for completed appointments.
          </p>
        </div>
        <PermissionGate permissions={["payments:write"]}>
          <Button type="button" onClick={() => setFormOpen(true)}>
            <Plus className="h-4 w-4" />
            Record payment
          </Button>
        </PermissionGate>
      </div>

      <Card>
        <CardHeader className="space-y-4">
          <CardTitle>Payment history</CardTitle>
          <div className="flex flex-col gap-3 sm:flex-row">
            <select
              value={methodFilter}
              onChange={(event) => {
                setMethodFilter(event.target.value as MethodFilter);
                setPage(1);
              }}
              className="h-10 rounded-md border border-input bg-background px-3 text-sm"
            >
              <option value="all">All methods</option>
              <option value="CASH">Cash</option>
              <option value="CARD">Card</option>
              <option value="UPI">UPI</option>
            </select>
            <select
              value={statusFilter}
              onChange={(event) => {
                setStatusFilter(event.target.value as StatusFilter);
                setPage(1);
              }}
              className="h-10 rounded-md border border-input bg-background px-3 text-sm"
            >
              <option value="all">All statuses</option>
              <option value="SUCCESS">Success</option>
              <option value="PENDING">Pending</option>
              <option value="FAILED">Failed</option>
              <option value="REFUNDED">Refunded</option>
            </select>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <PaymentsTable
            payments={paymentsQuery.data?.items ?? []}
            loading={paymentsQuery.isLoading}
            onView={openDetail}
            onPreviewInvoice={openInvoicePreview}
          />

          {paymentsQuery.data && paymentsQuery.data.total > paymentsQuery.data.limit ? (
            <div className="flex items-center justify-between border-t border-border pt-4">
              <p className="text-sm text-muted-foreground">
                Page {paymentsQuery.data.page} of {totalPages} · {paymentsQuery.data.total} payments
              </p>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((current) => current - 1)}
                >
                  Previous
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((current) => current + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <PaymentFormModal
        open={formOpen}
        appointments={completedAppointmentsQuery.data?.items ?? []}
        loading={isCreating}
        onOpenChange={setFormOpen}
        onSubmit={async (values) => {
          await createPayment(toPaymentCreatePayload(values));
          toast.success("Payment recorded");
        }}
      />

      <PaymentDetailModal
        open={detailOpen}
        payment={selectedPayment}
        onOpenChange={setDetailOpen}
        onPreviewInvoice={(payment) => {
          setDetailOpen(false);
          openInvoicePreview(payment);
        }}
      />

      <InvoicePreviewModal open={invoiceOpen} invoiceId={previewInvoiceId} onOpenChange={setInvoiceOpen} />
    </div>
  );
}
