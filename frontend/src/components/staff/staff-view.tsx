"use client";

import { useMemo, useState } from "react";
import { Plus, Search } from "lucide-react";

import { PermissionGate } from "@/components/auth/permission-gate";
import { DeactivateStaffDialog } from "@/components/staff/deactivate-staff-dialog";
import { StaffFormModal } from "@/components/staff/staff-form-modal";
import { StaffTable } from "@/components/staff/staff-table";
import { ErrorDisplay } from "@/components/feedback/error-display";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { usePermissions } from "@/hooks/use-permissions";
import { useStaff, useStaffMutations } from "@/hooks/use-staff";
import {
  toStaffCreatePayload,
  toStaffUpdatePayload,
  type StaffCreateFormValues,
  type StaffEditFormValues,
} from "@/lib/schemas/staff";
import { toast } from "@/lib/toast";
import type { StaffMember, StaffStatus } from "@/types/staff";

type StatusFilter = "all" | StaffStatus;

export function StaffView() {
  const { isAdmin } = usePermissions();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [page, setPage] = useState(1);
  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<"create" | "edit">("create");
  const [selectedStaff, setSelectedStaff] = useState<StaffMember | undefined>();
  const [deactivateOpen, setDeactivateOpen] = useState(false);
  const [staffToDeactivate, setStaffToDeactivate] = useState<StaffMember | undefined>();

  const listParams = useMemo(
    () => ({
      page,
      limit: 10,
      search: search.trim() || undefined,
      sort_by: "name",
      sort_order: "asc" as const,
      status: statusFilter === "all" ? undefined : statusFilter,
    }),
    [page, search, statusFilter],
  );

  const staffQuery = useStaff(listParams);
  const { createStaff, updateStaff, deactivateStaff, isCreating, isUpdating, isDeactivating } =
    useStaffMutations();

  const openCreate = () => {
    setFormMode("create");
    setSelectedStaff(undefined);
    setFormOpen(true);
  };

  const openEdit = (member: StaffMember) => {
    setFormMode("edit");
    setSelectedStaff(member);
    setFormOpen(true);
  };

  const openDeactivate = (member: StaffMember) => {
    setStaffToDeactivate(member);
    setDeactivateOpen(true);
  };

  if (staffQuery.isError) {
    return (
      <ErrorDisplay
        error={staffQuery.error}
        title="Unable to load staff"
        onRetry={() => staffQuery.refetch()}
      />
    );
  }

  const totalPages = staffQuery.data ? Math.ceil(staffQuery.data.total / staffQuery.data.limit) : 1;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Staff</h1>
          <p className="text-sm text-muted-foreground">Manage salon team members and commissions.</p>
        </div>
        <PermissionGate permissions={["staff:write"]}>
          <Button type="button" onClick={openCreate}>
            <Plus className="h-4 w-4" />
            Add staff
          </Button>
        </PermissionGate>
      </div>

      <Card>
        <CardHeader className="space-y-4">
          <CardTitle>Staff roster</CardTitle>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value);
                  setPage(1);
                }}
                placeholder="Search name, phone, designation"
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
              <option value="ACTIVE">Active</option>
              <option value="ON_LEAVE">On leave</option>
              <option value="INACTIVE">Inactive</option>
            </select>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <StaffTable
            staff={staffQuery.data?.items ?? []}
            loading={staffQuery.isLoading}
            onEdit={openEdit}
            onDeactivate={openDeactivate}
          />

          {staffQuery.data && staffQuery.data.total > staffQuery.data.limit ? (
            <div className="flex items-center justify-between border-t border-border pt-4">
              <p className="text-sm text-muted-foreground">
                Page {staffQuery.data.page} of {totalPages} · {staffQuery.data.total} staff
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

      <StaffFormModal
        open={formOpen}
        mode={formMode}
        staff={selectedStaff}
        loading={isCreating || isUpdating}
        onOpenChange={setFormOpen}
        onSubmit={async (values) => {
          if (formMode === "create") {
            await createStaff(toStaffCreatePayload(values as StaffCreateFormValues));
            toast.success("Staff member created");
          } else if (selectedStaff) {
            await updateStaff({
              id: selectedStaff.id,
              payload: toStaffUpdatePayload(values as StaffEditFormValues, isAdmin),
            });
            toast.success("Staff member updated");
          }
        }}
      />

      <DeactivateStaffDialog
        open={deactivateOpen}
        staffName={staffToDeactivate?.name}
        loading={isDeactivating}
        onOpenChange={setDeactivateOpen}
        onConfirm={async () => {
          if (!staffToDeactivate) {
            return;
          }
          await deactivateStaff(staffToDeactivate.id);
          toast.success("Staff member deactivated");
        }}
      />
    </div>
  );
}
