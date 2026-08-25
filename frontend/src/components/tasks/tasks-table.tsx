"use client";

import { Loader2 } from "lucide-react";

import { PermissionGate } from "@/components/auth/permission-gate";
import { TaskStatusBadge } from "@/components/tasks/task-status-badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { canAdvanceTaskStatus, getNextTaskStatus, getStatusActionLabel } from "@/lib/tasks/workflow";
import { formatShortDate } from "@/lib/format";
import type { Task } from "@/types/tasks";

interface TasksTableProps {
  tasks: Task[];
  loading?: boolean;
  updatingTaskId?: string;
  onAdvanceStatus: (task: Task) => void;
}

export function TasksTable({ tasks, loading, updatingTaskId, onAdvanceStatus }: TasksTableProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <Skeleton key={index} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border py-12 text-center">
        <p className="text-sm font-medium">No tasks found</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Assign chores to staff or adjust your filters.
        </p>
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Task</TableHead>
          <TableHead>Assigned to</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Due</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {tasks.map((task) => {
          const canAdvance = canAdvanceTaskStatus(task.status);
          const isUpdating = updatingTaskId === task.id;

          return (
            <TableRow key={task.id}>
              <TableCell>
                <div>
                  <p className="font-medium">{task.title}</p>
                  {task.description ? (
                    <p className="mt-0.5 line-clamp-1 text-xs text-muted-foreground">{task.description}</p>
                  ) : null}
                </div>
              </TableCell>
              <TableCell>{task.assigned_staff_name}</TableCell>
              <TableCell>
                <TaskStatusBadge status={task.status} />
              </TableCell>
              <TableCell>
                {task.due_date ? formatShortDate(task.due_date) : "—"}
              </TableCell>
              <TableCell className="text-right">
                <PermissionGate permissions={["tasks:write", "tasks:write_own"]} any>
                  {canAdvance ? (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      disabled={isUpdating}
                      onClick={() => onAdvanceStatus(task)}
                    >
                      {isUpdating ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          Updating
                        </>
                      ) : (
                        getStatusActionLabel(task.status)
                      )}
                    </Button>
                  ) : (
                    <span className="text-xs text-muted-foreground">
                      {getNextTaskStatus(task.status) ? "" : "Done"}
                    </span>
                  )}
                </PermissionGate>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
