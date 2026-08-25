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
  appointmentEditSchema,
  appointmentFormSchema,
  toAppointmentEditValues,
  toAppointmentFormValues,
  type AppointmentEditValues,
  type AppointmentFormValues,
} from "@/lib/schemas/appointment";
import { toast } from "@/lib/toast";
import type { Appointment } from "@/types/api";
import type { Customer } from "@/types/customers";
import type { Service } from "@/types/services";
import type { StaffMember } from "@/types/staff";

interface AppointmentFormProps {
  mode: "create" | "edit";
  appointment?: Appointment;
  customers: Customer[];
  staff: StaffMember[];
  services: Service[];
  defaults?: Partial<AppointmentFormValues>;
  loading?: boolean;
  onSubmit: (values: AppointmentFormValues | AppointmentEditValues) => Promise<void>;
  onCancel: () => void;
}

function ServiceChecklist({
  services,
  selectedServices,
  busy,
  onToggle,
  error,
}: {
  services: Service[];
  selectedServices: string[];
  busy: boolean;
  onToggle: (serviceId: string) => void;
  error?: string;
}) {
  return (
    <div className="space-y-2 sm:col-span-2">
      <Label>Services</Label>
      <div className="max-h-48 space-y-2 overflow-y-auto rounded-md border border-input p-3">
        {services.length === 0 ? (
          <p className="text-sm text-muted-foreground">No active services available.</p>
        ) : (
          services.map((service) => (
            <label key={service.id} className="flex cursor-pointer items-start gap-2 text-sm">
              <input
                type="checkbox"
                className="mt-0.5 h-4 w-4 rounded border-input"
                checked={selectedServices.includes(service.id)}
                disabled={busy}
                onChange={() => onToggle(service.id)}
              />
              <span>
                <span className="font-medium">{service.name}</span>
                <span className="text-muted-foreground">
                  {" "}
                  · {service.duration_minutes} min · ₹{service.price}
                </span>
              </span>
            </label>
          ))
        )}
      </div>
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
    </div>
  );
}

function CreateAppointmentForm({
  customers,
  staff,
  services,
  defaults,
  loading = false,
  onSubmit,
  onCancel,
}: Omit<AppointmentFormProps, "mode" | "appointment">) {
  const {
    register,
    handleSubmit,
    reset,
    setError,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<AppointmentFormValues>({
    resolver: zodResolver(appointmentFormSchema),
    defaultValues: toAppointmentFormValues(undefined, defaults),
  });

  const selectedServices = watch("service_ids") ?? [];

  useEffect(() => {
    reset(toAppointmentFormValues(undefined, defaults));
  }, [defaults, reset]);

  const toggleService = (serviceId: string) => {
    const next = selectedServices.includes(serviceId)
      ? selectedServices.filter((id) => id !== serviceId)
      : [...selectedServices, serviceId];
    setValue("service_ids", next, { shouldValidate: true });
  };

  const submit = async (values: AppointmentFormValues) => {
    try {
      await onSubmit(values);
    } catch (error) {
      const fieldErrors = getFieldErrors(error);
      for (const [field, message] of Object.entries(fieldErrors)) {
        if (field in appointmentFormSchema.shape) {
          setError(field as keyof AppointmentFormValues, { message });
        }
      }
      toast.fromError(error, getErrorMessage(error, "Unable to save appointment"));
    }
  };

  const busy = isSubmitting || loading;

  return (
    <form onSubmit={handleSubmit(submit)} className="space-y-4" noValidate>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2 sm:col-span-2">
          <Label htmlFor="customer_id">Customer</Label>
          <select
            id="customer_id"
            disabled={busy}
            className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
            {...register("customer_id")}
          >
            <option value="">Select customer</option>
            {customers.map((customer) => (
              <option key={customer.id} value={customer.id}>
                {customer.name} · {customer.phone}
              </option>
            ))}
          </select>
          {errors.customer_id ? (
            <p className="text-sm text-destructive">{errors.customer_id.message}</p>
          ) : null}
        </div>

        <div className="space-y-2 sm:col-span-2">
          <Label htmlFor="staff_id">Staff</Label>
          <select
            id="staff_id"
            disabled={busy}
            className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
            {...register("staff_id")}
          >
            <option value="">Select staff member</option>
            {staff.map((member) => (
              <option key={member.id} value={member.id}>
                {member.name} · {member.designation}
              </option>
            ))}
          </select>
          {errors.staff_id ? <p className="text-sm text-destructive">{errors.staff_id.message}</p> : null}
        </div>

        <div className="space-y-2">
          <Label htmlFor="appointment_date">Date</Label>
          <Input id="appointment_date" type="date" disabled={busy} {...register("appointment_date")} />
          {errors.appointment_date ? (
            <p className="text-sm text-destructive">{errors.appointment_date.message}</p>
          ) : null}
        </div>

        <div className="space-y-2">
          <Label htmlFor="start_time">Start time</Label>
          <Input id="start_time" type="time" disabled={busy} {...register("start_time")} />
          {errors.start_time ? (
            <p className="text-sm text-destructive">{errors.start_time.message}</p>
          ) : null}
        </div>

        <ServiceChecklist
          services={services}
          selectedServices={selectedServices}
          busy={busy}
          onToggle={toggleService}
          error={errors.service_ids?.message}
        />

        <div className="space-y-2 sm:col-span-2">
          <Label htmlFor="notes">Notes</Label>
          <Textarea id="notes" disabled={busy} rows={3} {...register("notes")} />
          {errors.notes ? <p className="text-sm text-destructive">{errors.notes.message}</p> : null}
        </div>
      </div>

      <div className="flex justify-end gap-2 border-t border-border pt-4">
        <Button type="button" variant="outline" disabled={busy} onClick={onCancel}>
          Close
        </Button>
        <Button type="submit" disabled={busy}>
          {busy ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Saving
            </>
          ) : (
            "Create appointment"
          )}
        </Button>
      </div>
    </form>
  );
}

function EditAppointmentForm({
  appointment,
  customers,
  staff,
  services,
  loading = false,
  onSubmit,
  onCancel,
}: Omit<AppointmentFormProps, "mode" | "defaults"> & { appointment: Appointment }) {
  const {
    register,
    handleSubmit,
    reset,
    setError,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<AppointmentEditValues>({
    resolver: zodResolver(appointmentEditSchema),
    defaultValues: toAppointmentEditValues(appointment),
  });

  const selectedServices = watch("service_ids") ?? [];

  useEffect(() => {
    reset(toAppointmentEditValues(appointment));
  }, [appointment, reset]);

  const toggleService = (serviceId: string) => {
    const next = selectedServices.includes(serviceId)
      ? selectedServices.filter((id) => id !== serviceId)
      : [...selectedServices, serviceId];
    setValue("service_ids", next, { shouldValidate: true });
  };

  const submit = async (values: AppointmentEditValues) => {
    try {
      await onSubmit(values);
    } catch (error) {
      const fieldErrors = getFieldErrors(error);
      for (const [field, message] of Object.entries(fieldErrors)) {
        if (field in appointmentEditSchema.shape) {
          setError(field as keyof AppointmentEditValues, { message });
        }
      }
      toast.fromError(error, getErrorMessage(error, "Unable to save appointment"));
    }
  };

  const busy = isSubmitting || loading;

  return (
    <form onSubmit={handleSubmit(submit)} className="space-y-4" noValidate>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2 sm:col-span-2">
          <Label htmlFor="customer_id">Customer</Label>
          <select
            id="customer_id"
            disabled={busy}
            className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
            {...register("customer_id")}
          >
            <option value="">Select customer</option>
            {customers.map((customer) => (
              <option key={customer.id} value={customer.id}>
                {customer.name} · {customer.phone}
              </option>
            ))}
          </select>
          {errors.customer_id ? (
            <p className="text-sm text-destructive">{errors.customer_id.message}</p>
          ) : null}
        </div>

        <div className="space-y-2 sm:col-span-2">
          <Label htmlFor="staff_id">Staff</Label>
          <select
            id="staff_id"
            disabled={busy}
            className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
            {...register("staff_id")}
          >
            <option value="">Select staff member</option>
            {staff.map((member) => (
              <option key={member.id} value={member.id}>
                {member.name} · {member.designation}
              </option>
            ))}
          </select>
          {errors.staff_id ? <p className="text-sm text-destructive">{errors.staff_id.message}</p> : null}
        </div>

        <ServiceChecklist
          services={services}
          selectedServices={selectedServices}
          busy={busy}
          onToggle={toggleService}
          error={errors.service_ids?.message}
        />

        <div className="space-y-2 sm:col-span-2">
          <Label htmlFor="notes">Notes</Label>
          <Textarea id="notes" disabled={busy} rows={3} {...register("notes")} />
          {errors.notes ? <p className="text-sm text-destructive">{errors.notes.message}</p> : null}
        </div>
      </div>

      <div className="flex justify-end gap-2 border-t border-border pt-4">
        <Button type="button" variant="outline" disabled={busy} onClick={onCancel}>
          Close
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

export function AppointmentForm(props: AppointmentFormProps) {
  if (props.mode === "edit" && props.appointment) {
    return <EditAppointmentForm {...props} appointment={props.appointment} />;
  }

  return <CreateAppointmentForm {...props} />;
}
