"use client";

import { useEffect } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { getErrorMessage, getFieldErrors } from "@/lib/api/errors";
import { tipEditSchema, toTipEditValues, type TipEditValues } from "@/lib/schemas/tip";
import { toast } from "@/lib/toast";
import type { Tip } from "@/types/tips";

interface TipEditFormProps {
  tip: Tip;
  loading?: boolean;
  onSubmit: (values: TipEditValues) => Promise<void>;
  onCancel: () => void;
}

export function TipEditForm({ tip, loading = false, onSubmit, onCancel }: TipEditFormProps) {
  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<TipEditValues>({
    resolver: zodResolver(tipEditSchema),
    defaultValues: toTipEditValues(tip),
  });

  useEffect(() => {
    reset(toTipEditValues(tip));
  }, [reset, tip]);

  const submit = async (values: TipEditValues) => {
    try {
      await onSubmit(values);
    } catch (error) {
      const fieldErrors = getFieldErrors(error);
      for (const [field, message] of Object.entries(fieldErrors)) {
        if (field in tipEditSchema.shape) {
          setError(field as keyof TipEditValues, { message });
        }
      }
      toast.fromError(error, getErrorMessage(error, "Unable to update tip"));
    }
  };

  const busy = isSubmitting || loading;

  return (
    <form onSubmit={handleSubmit(submit)} className="space-y-4" noValidate>
      <div className="rounded-md border border-border bg-muted/30 p-3 text-sm">
        <p className="font-medium">{tip.staff_name}</p>
        <p className="text-muted-foreground">Appointment {tip.appointment_id.slice(0, 8)}…</p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="edit_tip_amount">Amount (SAR)</Label>
        <Input
          id="edit_tip_amount"
          type="number"
          min={0.01}
          step="0.01"
          disabled={busy}
          {...register("amount")}
        />
        {errors.amount ? <p className="text-sm text-destructive">{errors.amount.message}</p> : null}
      </div>

      <div className="space-y-2">
        <Label htmlFor="edit_tip_notes">Notes</Label>
        <Textarea id="edit_tip_notes" rows={3} disabled={busy} {...register("notes")} />
        {errors.notes ? <p className="text-sm text-destructive">{errors.notes.message}</p> : null}
      </div>

      <div className="flex justify-end gap-2 border-t border-border pt-4">
        <Button type="button" variant="outline" disabled={busy} onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={busy}>
          {busy ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Saving
            </>
          ) : (
            "Save changes"
          )}
        </Button>
      </div>
    </form>
  );
}
