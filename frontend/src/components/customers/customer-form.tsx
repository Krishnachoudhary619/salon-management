"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { getErrorMessage, getFieldErrors } from "@/lib/api/errors";
import { customerFormSchema, type CustomerFormValues } from "@/lib/schemas/customer";
import { toast } from "@/lib/toast";

interface CustomerFormProps {
  loading?: boolean;
  onSubmit: (values: CustomerFormValues) => Promise<void>;
  onCancel: () => void;
}

export function CustomerForm({ loading, onSubmit, onCancel }: CustomerFormProps) {
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<CustomerFormValues>({
    resolver: zodResolver(customerFormSchema),
    defaultValues: {
      name: "",
      phone: "",
      email: "",
      notes: "",
    },
  });

  const submit = async (values: CustomerFormValues) => {
    try {
      await onSubmit(values);
    } catch (error) {
      const fieldErrors = getFieldErrors(error);
      for (const [field, message] of Object.entries(fieldErrors)) {
        if (field in customerFormSchema.shape) {
          setError(field as keyof CustomerFormValues, { message });
        }
      }
      toast.fromError(error, getErrorMessage(error, "Unable to save customer"));
    }
  };

  const busy = isSubmitting || loading;

  return (
    <form onSubmit={handleSubmit(submit)} className="space-y-4" noValidate>
      <div className="space-y-2">
        <Label htmlFor="customer_name">Name</Label>
        <Input id="customer_name" disabled={busy} placeholder="Full name" {...register("name")} />
        {errors.name ? <p className="text-sm text-destructive">{errors.name.message}</p> : null}
      </div>

      <div className="space-y-2">
        <Label htmlFor="customer_phone">Phone</Label>
        <Input
          id="customer_phone"
          disabled={busy}
          placeholder="10-digit mobile number"
          inputMode="numeric"
          {...register("phone")}
        />
        {errors.phone ? <p className="text-sm text-destructive">{errors.phone.message}</p> : null}
      </div>

      <div className="space-y-2">
        <Label htmlFor="customer_email">Email (optional)</Label>
        <Input id="customer_email" type="email" disabled={busy} placeholder="email@example.com" {...register("email")} />
        {errors.email ? <p className="text-sm text-destructive">{errors.email.message}</p> : null}
      </div>

      <div className="space-y-2">
        <Label htmlFor="customer_notes">Notes (optional)</Label>
        <Textarea
          id="customer_notes"
          disabled={busy}
          rows={3}
          placeholder="Preferences, allergies, or walk-in notes"
          {...register("notes")}
        />
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
            "Add customer"
          )}
        </Button>
      </div>
    </form>
  );
}
