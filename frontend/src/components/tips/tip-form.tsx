"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { getErrorMessage, getFieldErrors } from "@/lib/api/errors";
import { tipFormSchema, type TipFormValues } from "@/lib/schemas/tip";
import { formatShortDate, formatTime } from "@/lib/format";
import { toast } from "@/lib/toast";
import type { Appointment } from "@/types/api";

interface TipFormProps {
  appointments: Appointment[];
  loading?: boolean;
  onSubmit: (values: TipFormValues) => Promise<void>;
  onCancel: () => void;
}

export function TipForm({ appointments, loading = false, onSubmit, onCancel }: TipFormProps) {
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<TipFormValues>({
    resolver: zodResolver(tipFormSchema),
    defaultValues: {
      appointment_id: "",
      amount: 0,
      notes: "",
    },
  });

  const submit = async (values: TipFormValues) => {
    try {
      await onSubmit(values);
    } catch (error) {
      const fieldErrors = getFieldErrors(error);
      for (const [field, message] of Object.entries(fieldErrors)) {
        if (field in tipFormSchema.shape) {
          setError(field as keyof TipFormValues, { message });
        }
      }
      toast.fromError(error, getErrorMessage(error, "Unable to record tip"));
    }
  };

  const busy = isSubmitting || loading;

  return (
    <form onSubmit={handleSubmit(submit)} className="space-y-4" noValidate>
      <div className="space-y-2">
        <Label htmlFor="tip_appointment_id">Appointment</Label>
        <select
          id="tip_appointment_id"
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
          <p className="text-sm text-muted-foreground">No eligible appointments available.</p>
        ) : null}
      </div>

      <div className="space-y-2">
        <Label htmlFor="tip_amount">Amount (SAR)</Label>
        <Input id="tip_amount" type="number" min={0.01} step="0.01" disabled={busy} {...register("amount")} />
        {errors.amount ? <p className="text-sm text-destructive">{errors.amount.message}</p> : null}
      </div>

      <div className="space-y-2">
        <Label htmlFor="tip_notes">Notes (optional)</Label>
        <Textarea id="tip_notes" rows={3} disabled={busy} {...register("notes")} />
        {errors.notes ? <p className="text-sm text-destructive">{errors.notes.message}</p> : null}
      </div>

      <div className="flex justify-end gap-2 border-t border-border pt-4">
        <Button type="button" variant="outline" disabled={busy} onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={busy || appointments.length === 0}>
          {busy ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Recording
            </>
          ) : (
            "Record tip"
          )}
        </Button>
      </div>
    </form>
  );
}
