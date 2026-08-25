"use client";

import { useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";

import { AppointmentStatusBadge } from "@/components/dashboard/appointment-status-badge";
import { getInitials } from "@/components/dashboard/dashboard-utils";
import { ErrorDisplay } from "@/components/feedback/error-display";
import { PermissionGate } from "@/components/auth/permission-gate";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useAppointments } from "@/hooks/use-appointments";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { formatShortDate, formatTime } from "@/lib/format";
import type { Appointment } from "@/types/api";

const PAGE_SIZE = 15;

interface PendingAppointmentsPanelProps {
  staffId?: string;
  onSelect: (appointment: Appointment) => void;
  onConfirm: (appointment: Appointment) => void;
}

export function PendingAppointmentsPanel({ staffId, onSelect, onConfirm }: PendingAppointmentsPanelProps) {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const debouncedSearch = useDebouncedValue(search.trim(), 300);

  useEffect(() => {
    setPage(1);
  }, [staffId]);

  const listParams = useMemo(
    () => ({
      page,
      limit: PAGE_SIZE,
      status: "PENDING" as const,
      search: debouncedSearch || undefined,
      staff_id: staffId,
      sort_by: "appointment_date",
      sort_order: "asc" as const,
    }),
    [debouncedSearch, page, staffId],
  );

  const pendingQuery = useAppointments(listParams);
  const appointments = pendingQuery.data?.items ?? [];
  const total = pendingQuery.data?.total ?? 0;
  const totalPages = pendingQuery.data ? Math.max(1, Math.ceil(pendingQuery.data.total / pendingQuery.data.limit)) : 1;

  if (pendingQuery.isError) {
    return (
      <ErrorDisplay
        error={pendingQuery.error}
        title="Unable to load pending appointments"
        onRetry={() => pendingQuery.refetch()}
      />
    );
  }

  return (
    <Card className="rounded-2xl border-border/70 shadow-none">
      <CardHeader className="space-y-4">
        <div>
          <CardTitle className="text-base font-semibold">Pending appointments</CardTitle>
          <CardDescription>
            {total} waiting to be confirmed. Search by customer name or phone.
          </CardDescription>
        </div>
        <div className="relative max-w-xl">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
            placeholder="Search by name or phone"
            className="pl-9"
            aria-label="Search pending appointments"
          />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {pendingQuery.isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 6 }).map((_, index) => (
              <Skeleton key={index} className="h-16 w-full rounded-xl" />
            ))}
          </div>
        ) : appointments.length === 0 ? (
          <p className="rounded-xl bg-muted/40 px-4 py-10 text-center text-sm text-muted-foreground">
            {debouncedSearch
              ? "No pending appointments match that name or phone."
              : "There are no pending appointments."}
          </p>
        ) : (
          <ul className="divide-y divide-border/70">
            {appointments.map((appointment) => (
              <li key={appointment.id} className="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
                <button
                  type="button"
                  onClick={() => onSelect(appointment)}
                  className="flex min-w-0 flex-1 items-center gap-3 text-left"
                >
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-700">
                    {getInitials(appointment.customer_name)}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="truncate text-sm font-medium">{appointment.customer_name}</p>
                      <AppointmentStatusBadge status={appointment.status} />
                    </div>
                    <p className="mt-0.5 truncate text-xs text-muted-foreground">
                      {appointment.customer_phone} · {formatShortDate(appointment.appointment_date)} ·{" "}
                      {formatTime(appointment.start_time)} · {appointment.staff_name}
                    </p>
                  </div>
                </button>
                <PermissionGate permissions={["appointments:write", "appointments:write_own"]} any>
                  <Button
                    type="button"
                    size="sm"
                    className="shrink-0 rounded-full"
                    onClick={() => onConfirm(appointment)}
                  >
                    Confirm
                  </Button>
                </PermissionGate>
              </li>
            ))}
          </ul>
        )}

        {pendingQuery.data && pendingQuery.data.total > pendingQuery.data.limit ? (
          <div className="flex items-center justify-between border-t border-border pt-4">
            <p className="text-sm text-muted-foreground">
              Page {pendingQuery.data.page} of {totalPages} · {pendingQuery.data.total} pending
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
  );
}
