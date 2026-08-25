"use client";

import { useEffect, type ReactNode } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { usePermissions } from "@/hooks/use-permissions";
import { getErrorMessage, getFieldErrors } from "@/lib/api/errors";
import {
  staffCreateFormSchema,
  staffEditFormSchema,
  toStaffEditFormValues,
  type StaffCreateFormValues,
  type StaffEditFormValues,
} from "@/lib/schemas/staff";
import { toast } from "@/lib/toast";
import type { StaffMember, StaffStatus } from "@/types/staff";

interface StaffFormProps {
  mode: "create" | "edit";
  staff?: StaffMember;
  loading?: boolean;
  onSubmit: (values: StaffCreateFormValues | StaffEditFormValues) => Promise<void>;
  onCancel: () => void;
}

const STATUS_OPTIONS: StaffStatus[] = ["ACTIVE", "INACTIVE", "ON_LEAVE"];

export function StaffForm({ mode, staff, loading, onSubmit, onCancel }: StaffFormProps) {
  const { isAdmin } = usePermissions();
  const isCreate = mode === "create";

  const createForm = useForm<StaffCreateFormValues>({
    resolver: zodResolver(staffCreateFormSchema),
    defaultValues: {
      name: "",
      email: "",
      password: "",
      phone: "",
      designation: "",
      commission_percentage: 10,
      joining_date: new Date().toISOString().slice(0, 10),
      status: "ACTIVE",
    },
  });

  const editForm = useForm<StaffEditFormValues>({
    resolver: zodResolver(staffEditFormSchema),
    defaultValues: staff ? toStaffEditFormValues(staff) : undefined,
  });

  useEffect(() => {
    if (!isCreate && staff) {
      editForm.reset(toStaffEditFormValues(staff));
    }
  }, [editForm, isCreate, staff]);

  if (!isCreate && !staff) {
    return null;
  }

  const busy = (isCreate ? createForm.formState.isSubmitting : editForm.formState.isSubmitting) || Boolean(loading);

  const handleCreate = createForm.handleSubmit(async (values) => {
    try {
      await onSubmit(values);
    } catch (error) {
      for (const [field, message] of Object.entries(getFieldErrors(error))) {
        createForm.setError(field as keyof StaffCreateFormValues, { message });
      }
      toast.fromError(error, getErrorMessage(error, "Unable to save staff member"));
    }
  });

  const handleEdit = editForm.handleSubmit(async (values) => {
    try {
      await onSubmit(values);
    } catch (error) {
      for (const [field, message] of Object.entries(getFieldErrors(error))) {
        editForm.setError(field as keyof StaffEditFormValues, { message });
      }
      toast.fromError(error, getErrorMessage(error, "Unable to save staff member"));
    }
  });

  return (
    <form onSubmit={isCreate ? handleCreate : handleEdit} className="space-y-4" noValidate>
      <div className="grid gap-4 sm:grid-cols-2">
        {isCreate ? (
          <>
            <Field label="Name" error={createForm.formState.errors.name?.message}>
              <Input disabled={busy} {...createForm.register("name")} />
            </Field>
            <Field label="Email" error={createForm.formState.errors.email?.message}>
              <Input type="email" autoComplete="off" disabled={busy} {...createForm.register("email")} />
            </Field>
            <Field label="Password" error={createForm.formState.errors.password?.message}>
              <Input type="password" autoComplete="new-password" disabled={busy} {...createForm.register("password")} />
            </Field>
            <Field label="Phone" error={createForm.formState.errors.phone?.message}>
              <Input disabled={busy} placeholder="10 digit number" {...createForm.register("phone")} />
            </Field>
            <Field label="Designation" error={createForm.formState.errors.designation?.message}>
              <Input disabled={busy} placeholder="Senior Stylist" {...createForm.register("designation")} />
            </Field>
            {isAdmin ? (
              <Field label="Commission %" error={createForm.formState.errors.commission_percentage?.message}>
                <Input type="number" min={0} max={100} step="0.01" disabled={busy} {...createForm.register("commission_percentage")} />
              </Field>
            ) : null}
            <Field label="Joining date" error={createForm.formState.errors.joining_date?.message}>
              <Input type="date" disabled={busy} {...createForm.register("joining_date")} />
            </Field>
            <Field label="Status" error={createForm.formState.errors.status?.message}>
              <select
                disabled={busy}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                {...createForm.register("status")}
              >
                {STATUS_OPTIONS.map((status) => (
                  <option key={status} value={status}>
                    {status.replace("_", " ")}
                  </option>
                ))}
              </select>
            </Field>
          </>
        ) : (
          <>
            <Field label="Name" error={editForm.formState.errors.name?.message} className="sm:col-span-2">
              <Input disabled={busy} {...editForm.register("name")} />
            </Field>
            {staff?.email ? (
              <Field label="Email" className="sm:col-span-2">
                <Input value={staff.email} disabled readOnly />
              </Field>
            ) : null}
            <Field label="Phone" error={editForm.formState.errors.phone?.message}>
              <Input disabled={busy} placeholder="10 digit number" {...editForm.register("phone")} />
            </Field>
            <Field label="Designation" error={editForm.formState.errors.designation?.message}>
              <Input disabled={busy} placeholder="Senior Stylist" {...editForm.register("designation")} />
            </Field>
            {isAdmin ? (
              <Field label="Commission %" error={editForm.formState.errors.commission_percentage?.message}>
                <Input type="number" min={0} max={100} step="0.01" disabled={busy} {...editForm.register("commission_percentage")} />
              </Field>
            ) : null}
            <Field label="Joining date" error={editForm.formState.errors.joining_date?.message}>
              <Input type="date" disabled={busy} {...editForm.register("joining_date")} />
            </Field>
            <Field label="Status" error={editForm.formState.errors.status?.message}>
              <select
                disabled={busy}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                {...editForm.register("status")}
              >
                {STATUS_OPTIONS.map((status) => (
                  <option key={status} value={status}>
                    {status.replace("_", " ")}
                  </option>
                ))}
              </select>
            </Field>
          </>
        )}
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
          ) : isCreate ? (
            "Create staff"
          ) : (
            "Save changes"
          )}
        </Button>
      </div>
    </form>
  );
}

function Field({
  label,
  error,
  className,
  children,
}: {
  label: string;
  error?: string;
  className?: string;
  children: ReactNode;
}) {
  return (
    <div className={`space-y-2 ${className ?? ""}`}>
      <Label>{label}</Label>
      {children}
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
    </div>
  );
}
