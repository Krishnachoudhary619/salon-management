"use client";

import { useEffect } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { getErrorMessage, getFieldErrors } from "@/lib/api/errors";
import {
  rescheduleFormSchema,
  toRescheduleFormValues,
  type RescheduleFormValues,
} from "@/lib/schemas/appointment";
import { toast } from "@/lib/toast";
import type { Appointment } from "@/types/api";
import type { StaffMember } from "@/types/staff";

interface RescheduleFormProps {
  appointment: Appointment;
  staff: StaffMember[];
  loading?: boolean;
  onSubmit: (values: RescheduleFormValues) => Promise<void>;
  onCancel: () => void;
}

export function RescheduleForm({ appointment, staff, loading, onSubmit, onCancel }: RescheduleFormProps) {
  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<RescheduleFormValues>({
    resolver: zodResolver(rescheduleFormSchema),
    defaultValues: toRescheduleFormValues(appointment),
  });

  useEffect(() => {
    reset(toRescheduleFormValues(appointment));
  }, [appointment, reset]);

  const submit = async (values: RescheduleFormValues) => {
    try {
      await onSubmit(values);
    } catch (error) {
      const fieldErrors = getFieldErrors(error);
      for (const [field, message] of Object.entries(fieldErrors)) {
        if (field in rescheduleFormSchema.shape) {
          setError(field as keyof RescheduleFormValues, { message });
        }
      }
      toast.fromError(error, getErrorMessage(error, "Unable to reschedule appointment"));
    }
  };

  const busy = isSubmitting || loading;

  return (
    <form onSubmit={handleSubmit(submit)} className="space-y-4" noValidate>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="reschedule_date">Date</Label>
          <Input id="reschedule_date" type="date" disabled={busy} {...register("appointment_date")} />
          {errors.appointment_date ? (
            <p className="text-sm text-destructive">{errors.appointment_date.message}</p>
          ) : null}
        </div>

        <div className="space-y-2">
          <Label htmlFor="reschedule_time">Start time</Label>
          <Input id="reschedule_time" type="time" disabled={busy} {...register("start_time")} />
          {errors.start_time ? (
            <p className="text-sm text-destructive">{errors.start_time.message}</p>
          ) : null}
        </div>

        <div className="space-y-2 sm:col-span-2">
          <Label htmlFor="reschedule_staff">Staff (optional)</Label>
          <select
            id="reschedule_staff"
            disabled={busy}
            className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
            {...register("staff_id")}
          >
            <option value="">Keep current staff</option>
            {staff.map((member) => (
              <option key={member.id} value={member.id}>
                {member.name} · {member.designation}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex justify-end gap-2 border-t border-border pt-4">
        <Button type="button" variant="outline" disabled={busy} onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={busy}>
          {busy ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Rescheduling
            </>
          ) : (
            "Reschedule"
          )}
        </Button>
      </div>
    </form>
  );
}
