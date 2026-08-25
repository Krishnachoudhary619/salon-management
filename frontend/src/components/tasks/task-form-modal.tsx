"use client";

import { Dialog } from "@/components/ui/dialog";
import { TaskForm } from "@/components/tasks/task-form";
import type { TaskFormValues } from "@/lib/schemas/task";
import type { StaffMember } from "@/types/staff";

interface TaskFormModalProps {
  open: boolean;
  staff: StaffMember[];
  loading?: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (values: TaskFormValues) => Promise<void>;
}

export function TaskFormModal({
  open,
  staff,
  loading,
  onOpenChange,
  onSubmit,
}: TaskFormModalProps) {
  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Assign task"
      description="Create a new task for a staff member. Tasks start as Pending."
      className="max-w-lg"
    >
      <TaskForm
        staff={staff}
        loading={loading}
        onCancel={() => onOpenChange(false)}
        onSubmit={async (values) => {
          await onSubmit(values);
          onOpenChange(false);
        }}
      />
    </Dialog>
  );
}
