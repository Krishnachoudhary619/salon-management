"use client";

import { useEffect } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";

import { LoadingSpinner } from "@/components/feedback/loading-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useInvoiceByAppointment } from "@/hooks/use-invoices";
import { getErrorMessage, getFieldErrors } from "@/lib/api/errors";
import {
  getRemainingBalance,
  PAYMENT_METHODS,
  paymentFormSchema,
  type PaymentFormValues,
} from "@/lib/schemas/payment";
import { formatCurrency, formatShortDate, formatTime } from "@/lib/format";
import { toast } from "@/lib/toast";
import type { Appointment } from "@/types/api";

interface PaymentFormProps {
  appointments: Appointment[];
  loading?: boolean;
  onSubmit: (values: PaymentFormValues) => Promise<void>;
  onCancel: () => void;
}

export function PaymentForm({ appointments, loading = false, onSubmit, onCancel }: PaymentFormProps) {
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<PaymentFormValues>({
    resolver: zodResolver(paymentFormSchema),
    defaultValues: {
      appointment_id: "",
      amount: 0,
      payment_method: "CASH",
    },
  });

  const appointmentId = watch("appointment_id");
  const invoiceQuery = useInvoiceByAppointment(appointmentId || undefined);
  const selectedAppointment = appointments.find((item) => item.id === appointmentId);

  useEffect(() => {
    if (invoiceQuery.data) {
      const remaining = getRemainingBalance(invoiceQuery.data.total, invoiceQuery.data.paid_amount);
      if (remaining > 0) {
        setValue("amount", remaining);
      }
    }
  }, [invoiceQuery.data, setValue]);

  const submit = async (values: PaymentFormValues) => {
    try {
      await onSubmit(values);
    } catch (error) {
      const fieldErrors = getFieldErrors(error);
      for (const [field, message] of Object.entries(fieldErrors)) {
        if (field in paymentFormSchema.shape) {
          setError(field as keyof PaymentFormValues, { message });
        }
      }
      toast.fromError(error, getErrorMessage(error, "Unable to record payment"));
    }
  };

  const busy = isSubmitting || loading;
  const remaining = invoiceQuery.data
    ? getRemainingBalance(invoiceQuery.data.total, invoiceQuery.data.paid_amount)
    : null;

  return (
    <form onSubmit={handleSubmit(submit)} className="space-y-4" noValidate>
      <div className="space-y-2">
        <Label htmlFor="appointment_id">Completed appointment</Label>
        <select
          id="appointment_id"
          disabled={busy}
          className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
          {...register("appointment_id")}
        >
          <option value="">Select appointment</option>
          {appointments.map((appointment) => (
            <option key={appointment.id} value={appointment.id}>
              {appointment.customer_name} · {formatShortDate(appointment.appointment_date)} ·{" "}
              {formatTime(appointment.start_time)} · {appointment.staff_name}
            </option>
          ))}
        </select>
        {errors.appointment_id ? (
          <p className="text-sm text-destructive">{errors.appointment_id.message}</p>
        ) : null}
        {appointments.length === 0 ? (
          <p className="text-sm text-muted-foreground">No completed appointments available for payment.</p>
        ) : null}
      </div>

      {appointmentId ? (
        invoiceQuery.isLoading ? (
          <LoadingSpinner label="Loading invoice" />
        ) : invoiceQuery.data ? (
          <div className="rounded-md border border-border bg-muted/30 p-4 text-sm">
            <dl className="grid gap-2 sm:grid-cols-2">
              <div>
                <dt className="text-muted-foreground">Invoice</dt>
                <dd className="font-medium">{invoiceQuery.data.invoice_number}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Total</dt>
                <dd className="font-medium">{formatCurrency(invoiceQuery.data.total)}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Paid</dt>
                <dd className="font-medium">{formatCurrency(invoiceQuery.data.paid_amount)}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Remaining</dt>
                <dd className="font-medium">
                  {remaining !== null ? formatCurrency(remaining) : "—"}
                  {invoiceQuery.data.is_paid ? (
                    <span className="ml-2 text-emerald-600">(Fully paid)</span>
                  ) : null}
                </dd>
              </div>
            </dl>
            {selectedAppointment ? (
              <p className="mt-3 text-muted-foreground">
                {selectedAppointment.customer_name} with {selectedAppointment.staff_name}
              </p>
            ) : null}
          </div>
        ) : (
          <p className="text-sm text-destructive">
            No invoice found for this appointment. Complete the appointment first.
          </p>
        )
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="amount">Amount (INR)</Label>
          <Input
            id="amount"
            type="number"
            min={0.01}
            step="0.01"
            disabled={busy || !invoiceQuery.data || invoiceQuery.data.is_paid}
            {...register("amount")}
          />
          {errors.amount ? <p className="text-sm text-destructive">{errors.amount.message}</p> : null}
        </div>

        <div className="space-y-2">
          <Label htmlFor="payment_method">Payment method</Label>
          <select
            id="payment_method"
            disabled={busy || !invoiceQuery.data || invoiceQuery.data.is_paid}
            className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
            {...register("payment_method")}
          >
            {PAYMENT_METHODS.map((method) => (
              <option key={method} value={method}>
                {method}
              </option>
            ))}
          </select>
          {errors.payment_method ? (
            <p className="text-sm text-destructive">{errors.payment_method.message}</p>
          ) : null}
        </div>
      </div>

      <div className="flex justify-end gap-2 border-t border-border pt-4">
        <Button type="button" variant="outline" disabled={busy} onClick={onCancel}>
          Cancel
        </Button>
        <Button
          type="submit"
          disabled={busy || !invoiceQuery.data || invoiceQuery.data.is_paid}
        >
          {busy ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Recording
            </>
          ) : (
            "Record payment"
          )}
        </Button>
      </div>
    </form>
  );
}
