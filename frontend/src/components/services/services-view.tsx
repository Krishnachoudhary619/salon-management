"use client";

import { useMemo, useState } from "react";
import { Plus, Search } from "lucide-react";

import { PermissionGate } from "@/components/auth/permission-gate";
import { DeactivateServiceDialog } from "@/components/services/deactivate-service-dialog";
import { ServiceFormModal } from "@/components/services/service-form-modal";
import { ServicesTable } from "@/components/services/services-table";
import { ErrorDisplay } from "@/components/feedback/error-display";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useServiceMutations, useServices } from "@/hooks/use-services";
import { toServiceCreatePayload, toServiceUpdatePayload } from "@/lib/schemas/service";
import { toast } from "@/lib/toast";
import type { Service } from "@/types/services";

type StatusFilter = "all" | "active" | "inactive";

export function ServicesView() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [page, setPage] = useState(1);
  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<"create" | "edit">("create");
  const [selectedService, setSelectedService] = useState<Service | undefined>();
  const [deactivateOpen, setDeactivateOpen] = useState(false);
  const [serviceToDeactivate, setServiceToDeactivate] = useState<Service | undefined>();

  const listParams = useMemo(
    () => ({
      page,
      limit: 10,
      search: search.trim() || undefined,
      sort_by: "name",
      sort_order: "asc" as const,
      is_active: statusFilter === "all" ? undefined : statusFilter === "active",
    }),
    [page, search, statusFilter],
  );

  const servicesQuery = useServices(listParams);
  const { createService, updateService, deactivateService, isCreating, isUpdating, isDeactivating } =
    useServiceMutations();

  const openCreate = () => {
    setFormMode("create");
    setSelectedService(undefined);
    setFormOpen(true);
  };

  const openEdit = (service: Service) => {
    setFormMode("edit");
    setSelectedService(service);
    setFormOpen(true);
  };

  const openDeactivate = (service: Service) => {
    setServiceToDeactivate(service);
    setDeactivateOpen(true);
  };

  if (servicesQuery.isError) {
    return (
      <ErrorDisplay
        error={servicesQuery.error}
        title="Unable to load services"
        onRetry={() => servicesQuery.refetch()}
      />
    );
  }

  const totalPages = servicesQuery.data ? Math.ceil(servicesQuery.data.total / servicesQuery.data.limit) : 1;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Services</h1>
          <p className="text-sm text-muted-foreground">Manage the salon service catalog.</p>
        </div>
        <PermissionGate permissions={["services:write"]}>
          <Button type="button" onClick={openCreate}>
            <Plus className="h-4 w-4" />
            Add service
          </Button>
        </PermissionGate>
      </div>

      <Card>
        <CardHeader className="space-y-4">
          <CardTitle>Service catalog</CardTitle>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value);
                  setPage(1);
                }}
                placeholder="Search name, category, description"
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
              <option value="active">Active only</option>
              <option value="inactive">Inactive only</option>
            </select>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <ServicesTable
            services={servicesQuery.data?.items ?? []}
            loading={servicesQuery.isLoading}
            onEdit={openEdit}
            onDeactivate={openDeactivate}
          />

          {servicesQuery.data && servicesQuery.data.total > servicesQuery.data.limit ? (
            <div className="flex items-center justify-between border-t border-border pt-4">
              <p className="text-sm text-muted-foreground">
                Page {servicesQuery.data.page} of {totalPages} · {servicesQuery.data.total} services
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

      <ServiceFormModal
        open={formOpen}
        mode={formMode}
        service={selectedService}
        loading={isCreating || isUpdating}
        onOpenChange={setFormOpen}
        onSubmit={async (values) => {
          if (formMode === "create") {
            await createService(toServiceCreatePayload(values));
            toast.success("Service created");
          } else if (selectedService) {
            await updateService({
              id: selectedService.id,
              payload: toServiceUpdatePayload(values),
            });
            toast.success("Service updated");
          }
        }}
      />

      <DeactivateServiceDialog
        open={deactivateOpen}
        serviceName={serviceToDeactivate?.name}
        loading={isDeactivating}
        onOpenChange={setDeactivateOpen}
        onConfirm={async () => {
          if (!serviceToDeactivate) {
            return;
          }
          await deactivateService(serviceToDeactivate.id);
          toast.success("Service deactivated");
        }}
      />
    </div>
  );
}
