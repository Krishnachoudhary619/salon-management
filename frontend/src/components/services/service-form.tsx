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
import {
  serviceFormSchema,
  toServiceCreatePayload,
  toServiceFormValues,
  toServiceUpdatePayload,
  type ServiceFormValues,
} from "@/lib/schemas/service";
import { toast } from "@/lib/toast";
import type { Service } from "@/types/services";

interface ServiceFormProps {
  mode: "create" | "edit";
  service?: Service;
  loading?: boolean;
  onSubmit: (values: ServiceFormValues) => Promise<void>;
  onCancel: () => void;
}

export function ServiceForm({ mode, service, loading, onSubmit, onCancel }: ServiceFormProps) {
  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<ServiceFormValues>({
    resolver: zodResolver(serviceFormSchema),
    defaultValues: {
      name: "",
      description: "",
      category: "",
      duration_minutes: 30,
      price: 100,
      is_active: true,
    },
  });

  useEffect(() => {
    if (service) {
      reset(toServiceFormValues(service));
    } else {
      reset({
        name: "",
        description: "",
        category: "",
        duration_minutes: 30,
        price: 100,
        is_active: true,
      });
    }
  }, [reset, service]);

  const submit = async (values: ServiceFormValues) => {
    try {
      await onSubmit(values);
    } catch (error) {
      const fieldErrors = getFieldErrors(error);
      for (const [field, message] of Object.entries(fieldErrors)) {
        if (field in serviceFormSchema.shape) {
          setError(field as keyof ServiceFormValues, { message });
        }
      }
      toast.fromError(error, getErrorMessage(error, "Unable to save service"));
    }
  };

  const busy = isSubmitting || loading;

  return (
    <form onSubmit={handleSubmit(submit)} className="space-y-4" noValidate>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2 sm:col-span-2">
          <Label htmlFor="name">Name</Label>
          <Input id="name" disabled={busy} {...register("name")} />
          {errors.name ? <p className="text-sm text-destructive">{errors.name.message}</p> : null}
        </div>

        <div className="space-y-2 sm:col-span-2">
          <Label htmlFor="category">Category</Label>
          <Input id="category" disabled={busy} placeholder="Hair, Skin, Nails" {...register("category")} />
          {errors.category ? (
            <p className="text-sm text-destructive">{errors.category.message}</p>
          ) : null}
        </div>

        <div className="space-y-2">
          <Label htmlFor="duration_minutes">Duration (minutes)</Label>
          <Input
            id="duration_minutes"
            type="number"
            min={1}
            disabled={busy}
            {...register("duration_minutes")}
          />
          {errors.duration_minutes ? (
            <p className="text-sm text-destructive">{errors.duration_minutes.message}</p>
          ) : null}
        </div>

        <div className="space-y-2">
          <Label htmlFor="price">Price (INR)</Label>
          <Input id="price" type="number" min={0.01} step="0.01" disabled={busy} {...register("price")} />
          {errors.price ? <p className="text-sm text-destructive">{errors.price.message}</p> : null}
        </div>

        <div className="space-y-2 sm:col-span-2">
          <Label htmlFor="description">Description</Label>
          <Textarea id="description" disabled={busy} rows={3} {...register("description")} />
          {errors.description ? (
            <p className="text-sm text-destructive">{errors.description.message}</p>
          ) : null}
        </div>

        <div className="flex items-center gap-2 sm:col-span-2">
          <input id="is_active" type="checkbox" disabled={busy} className="h-4 w-4 rounded border-input" {...register("is_active")} />
          <Label htmlFor="is_active">Active (available for new bookings)</Label>
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
              Saving
            </>
          ) : mode === "create" ? (
            "Create service"
          ) : (
            "Save changes"
          )}
        </Button>
      </div>
    </form>
  );
}

export { toServiceCreatePayload, toServiceUpdatePayload };
