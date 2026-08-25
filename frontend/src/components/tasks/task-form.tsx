"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { getErrorMessage, getFieldErrors } from "@/lib/api/errors";
import { taskFormSchema, type TaskFormValues } from "@/lib/schemas/task";
import { toast } from "@/lib/toast";
import type { StaffMember } from "@/types/staff";

interface TaskFormProps {
  staff: StaffMember[];
  loading?: boolean;
  onSubmit: (values: TaskFormValues) => Promise<void>;
  onCancel: () => void;
}

export function TaskForm({ staff, loading = false, onSubmit, onCancel }: TaskFormProps) {
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<TaskFormValues>({
    resolver: zodResolver(taskFormSchema),
    defaultValues: {
      assigned_staff_id: "",
      title: "",
      description: "",
      due_date: "",
    },
  });

  const submit = async (values: TaskFormValues) => {
    try {
      await onSubmit(values);
    } catch (error) {
      const fieldErrors = getFieldErrors(error);
      for (const [field, message] of Object.entries(fieldErrors)) {
        if (field in taskFormSchema.shape) {
          setError(field as keyof TaskFormValues, { message });
        }
      }
      toast.fromError(error, getErrorMessage(error, "Unable to create task"));
    }
  };

  const busy = isSubmitting || loading;

  return (
    <form onSubmit={handleSubmit(submit)} className="space-y-4" noValidate>
      <div className="space-y-2">
        <Label htmlFor="assigned_staff_id">Assign to</Label>
        <select
          id="assigned_staff_id"
          disabled={busy}
          className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
          {...register("assigned_staff_id")}
        >
          <option value="">Select staff member</option>
          {staff.map((member) => (
            <option key={member.id} value={member.id}>
              {member.name} · {member.designation}
            </option>
          ))}
        </select>
        {errors.assigned_staff_id ? (
          <p className="text-sm text-destructive">{errors.assigned_staff_id.message}</p>
        ) : null}
      </div>

      <div className="space-y-2">
        <Label htmlFor="task_title">Title</Label>
        <Input id="task_title" disabled={busy} {...register("title")} />
        {errors.title ? <p className="text-sm text-destructive">{errors.title.message}</p> : null}
      </div>

      <div className="space-y-2">
        <Label htmlFor="task_description">Description (optional)</Label>
        <Textarea id="task_description" rows={3} disabled={busy} {...register("description")} />
        {errors.description ? (
          <p className="text-sm text-destructive">{errors.description.message}</p>
        ) : null}
      </div>

      <div className="space-y-2">
        <Label htmlFor="task_due_date">Due date (optional)</Label>
        <Input id="task_due_date" type="date" disabled={busy} {...register("due_date")} />
        {errors.due_date ? <p className="text-sm text-destructive">{errors.due_date.message}</p> : null}
      </div>

      <div className="flex justify-end gap-2 border-t border-border pt-4">
        <Button type="button" variant="outline" disabled={busy} onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={busy}>
          {busy ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Assigning
            </>
          ) : (
            "Assign task"
          )}
        </Button>
      </div>
    </form>
  );
}
