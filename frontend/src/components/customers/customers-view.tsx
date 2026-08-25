"use client";

import { useMemo, useState } from "react";
import { Plus, Search } from "lucide-react";

import { CustomerFormModal } from "@/components/customers/customer-form-modal";
import { CustomersTable } from "@/components/customers/customers-table";
import { PermissionGate } from "@/components/auth/permission-gate";
import { ErrorDisplay } from "@/components/feedback/error-display";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useCustomerMutations, useCustomers } from "@/hooks/use-customers";
import { toCustomerCreatePayload } from "@/lib/schemas/customer";
import { toast } from "@/lib/toast";

export function CustomersView() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [formOpen, setFormOpen] = useState(false);

  const listParams = useMemo(
    () => ({
      page,
      limit: 10,
      search: search.trim() || undefined,
      sort_by: "last_visit",
      sort_order: "desc" as const,
    }),
    [page, search],
  );

  const customersQuery = useCustomers(listParams);
  const { createCustomer, isCreating } = useCustomerMutations();

  if (customersQuery.isError) {
    return (
      <ErrorDisplay
        error={customersQuery.error}
        title="Unable to load customers"
        onRetry={() => customersQuery.refetch()}
      />
    );
  }

  const totalPages = customersQuery.data
    ? Math.ceil(customersQuery.data.total / customersQuery.data.limit)
    : 1;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Customers</h1>
          <p className="text-sm text-muted-foreground">
            Search customer profiles or register walk-ins before booking.
          </p>
        </div>
        <PermissionGate permissions={["customers:write"]}>
          <Button type="button" onClick={() => setFormOpen(true)}>
            <Plus className="h-4 w-4" />
            Add customer
          </Button>
        </PermissionGate>
      </div>

      <Card>
        <CardHeader className="space-y-4">
          <CardTitle>Customer directory</CardTitle>
          <div className="relative max-w-xl">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setPage(1);
              }}
              placeholder="Search by name, phone, or email"
              className="pl-9"
            />
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <CustomersTable customers={customersQuery.data?.items ?? []} loading={customersQuery.isLoading} />

          {customersQuery.data && customersQuery.data.total > customersQuery.data.limit ? (
            <div className="flex items-center justify-between border-t border-border pt-4">
              <p className="text-sm text-muted-foreground">
                Page {customersQuery.data.page} of {totalPages} · {customersQuery.data.total} customers
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

      <CustomerFormModal
        open={formOpen}
        loading={isCreating}
        onOpenChange={setFormOpen}
        onSubmit={async (values) => {
          await createCustomer(toCustomerCreatePayload(values));
          toast.success("Customer added");
        }}
      />
    </div>
  );
}
