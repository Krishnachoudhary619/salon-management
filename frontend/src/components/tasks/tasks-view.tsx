"use client";

import { useMemo, useState } from "react";
import { Plus, Search } from "lucide-react";

import { PermissionGate } from "@/components/auth/permission-gate";
import { TaskFormModal } from "@/components/tasks/task-form-modal";
import { TasksTable } from "@/components/tasks/tasks-table";
import { ErrorDisplay } from "@/components/feedback/error-display";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { usePermissions } from "@/hooks/use-permissions";
import { useStaff } from "@/hooks/use-staff";
import { useTaskMutations, useTasks } from "@/hooks/use-tasks";
import { getNextTaskStatus } from "@/lib/tasks/workflow";
import { toTaskCreatePayload, toTaskStatusUpdatePayload } from "@/lib/schemas/task";
import { toast } from "@/lib/toast";
import type { Task, TaskStatus } from "@/types/tasks";

type StatusFilter = TaskStatus | "all";

export function TasksView() {
  const { canOne } = usePermissions();
  const canFilterStaff = canOne("tasks:read");

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [staffFilter, setStaffFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [formOpen, setFormOpen] = useState(false);
  const [updatingTaskId, setUpdatingTaskId] = useState<string | undefined>();

  const listParams = useMemo(
    () => ({
      page,
      limit: 10,
      sort_by: "created_at",
      sort_order: "desc" as const,
      assigned_staff_id: staffFilter || undefined,
      status: statusFilter === "all" ? undefined : statusFilter,
      search: search.trim() || undefined,
    }),
    [page, search, staffFilter, statusFilter],
  );

  const tasksQuery = useTasks(listParams);
  const staffQuery = useStaff({ page: 1, limit: 100, sort_by: "name", sort_order: "asc", status: "ACTIVE" });
  const { createTask, updateTask, isCreating, isUpdating } = useTaskMutations();

  const handleAdvanceStatus = async (task: Task) => {
    const nextStatus = getNextTaskStatus(task.status);
    if (!nextStatus) {
      return;
    }

    setUpdatingTaskId(task.id);
    try {
      await updateTask({ id: task.id, payload: toTaskStatusUpdatePayload(nextStatus) });
      toast.success(`Task marked ${nextStatus.toLowerCase().replace("_", " ")}`);
    } catch (error) {
      toast.fromError(error, "Unable to update task status");
    } finally {
      setUpdatingTaskId(undefined);
    }
  };

  if (tasksQuery.isError) {
    return (
      <ErrorDisplay
        error={tasksQuery.error}
        title="Unable to load tasks"
        onRetry={() => tasksQuery.refetch()}
      />
    );
  }

  const totalPages = tasksQuery.data ? Math.ceil(tasksQuery.data.total / tasksQuery.data.limit) : 1;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Tasks</h1>
          <p className="text-sm text-muted-foreground">
            Staff chores with one-way status flow: Pending → In progress → Completed.
          </p>
        </div>
        <PermissionGate permissions={["tasks:write"]}>
          <Button type="button" onClick={() => setFormOpen(true)}>
            <Plus className="h-4 w-4" />
            Assign task
          </Button>
        </PermissionGate>
      </div>

      <Card>
        <CardHeader className="space-y-4">
          <CardTitle>Task list</CardTitle>
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value);
                  setPage(1);
                }}
                placeholder="Search title or description"
                className="pl-9"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(event) => {
                setStatusFilter(event.target.value as StatusFilter);
                setPage(1);
              }}
              className="h-10 rounded-md border border-input bg-background px-3 text-sm"
            >
              <option value="all">All statuses</option>
              <option value="PENDING">Pending</option>
              <option value="IN_PROGRESS">In progress</option>
              <option value="COMPLETED">Completed</option>
            </select>
            {canFilterStaff ? (
              <select
                value={staffFilter}
                onChange={(event) => {
                  setStaffFilter(event.target.value);
                  setPage(1);
                }}
                className="h-10 rounded-md border border-input bg-background px-3 text-sm lg:min-w-56"
              >
                <option value="">All staff</option>
                {(staffQuery.data?.items ?? []).map((member) => (
                  <option key={member.id} value={member.id}>
                    {member.name}
                  </option>
                ))}
              </select>
            ) : null}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <TasksTable
            tasks={tasksQuery.data?.items ?? []}
            loading={tasksQuery.isLoading}
            updatingTaskId={isUpdating ? updatingTaskId : undefined}
            onAdvanceStatus={handleAdvanceStatus}
          />

          {tasksQuery.data && tasksQuery.data.total > tasksQuery.data.limit ? (
            <div className="flex items-center justify-between border-t border-border pt-4">
              <p className="text-sm text-muted-foreground">
                Page {tasksQuery.data.page} of {totalPages} · {tasksQuery.data.total} tasks
              </p>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((current) => current - 1)}
                >
                  Previous
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((current) => current + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <TaskFormModal
        open={formOpen}
        staff={staffQuery.data?.items ?? []}
        loading={isCreating}
        onOpenChange={setFormOpen}
        onSubmit={async (values) => {
          await createTask(toTaskCreatePayload(values));
          toast.success("Task assigned");
        }}
      />
    </div>
  );
}
