"use client";

import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, ArrowRight, Check, Loader2, Search } from "lucide-react";

import { BookingStepIndicator } from "@/components/appointments/booking-step-indicator";
import { ErrorDisplay } from "@/components/feedback/error-display";
import { LoadingSpinner } from "@/components/feedback/loading-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useAvailability } from "@/hooks/use-availability";
import { toTimeInputValue } from "@/lib/appointments/calendar-utils";
import {
  BOOKING_STEPS,
  createEmptyBookingDraft,
  getNextBookingStep,
  getPreviousBookingStep,
  getTodayIsoDate,
  getTotalServiceDuration,
  isTimeSlotAvailable,
  toBookingAppointmentCreatePayload,
  validateBookingStep,
  type BookingDraft,
  type BookingStep,
  type CustomerMode,
} from "@/lib/schemas/booking-wizard";
import { bookingNewCustomerSchema, createEmptyNewCustomer } from "@/lib/schemas/customer";
import { formatCurrency, formatShortDate, formatTime } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Customer } from "@/types/customers";
import type { Service } from "@/types/services";
import type { StaffMember } from "@/types/staff";

interface BookingWizardProps {
  customers: Customer[];
  staff: StaffMember[];
  services: Service[];
  defaults?: Partial<BookingDraft>;
  loading?: boolean;
  onCancel: () => void;
  onSubmit: (payload: ReturnType<typeof toBookingAppointmentCreatePayload>) => Promise<void>;
}

export function BookingWizard({
  customers,
  staff,
  services,
  defaults,
  loading = false,
  onCancel,
  onSubmit,
}: BookingWizardProps) {
  const [step, setStep] = useState<BookingStep>("customer");
  const [draft, setDraft] = useState<BookingDraft>(() => createEmptyBookingDraft(defaults));
  const [stepError, setStepError] = useState<string | null>(null);
  const [customerSearch, setCustomerSearch] = useState("");

  useEffect(() => {
    setDraft(createEmptyBookingDraft(defaults));
    setStep("customer");
    setStepError(null);
    setCustomerSearch("");
  }, [defaults]);

  const totalDuration = useMemo(
    () => getTotalServiceDuration(draft.service_ids, services),
    [draft.service_ids, services],
  );

  const availabilityParams =
    step === "time" && draft.staff_id && draft.appointment_date && totalDuration > 0
      ? {
          staff_id: draft.staff_id,
          date: draft.appointment_date,
          duration_minutes: totalDuration,
        }
      : null;

  const availabilityQuery = useAvailability(availabilityParams);

  const filteredCustomers = useMemo(() => {
    const query = customerSearch.trim().toLowerCase();
    if (!query) {
      return customers;
    }
    return customers.filter(
      (customer) =>
        customer.name.toLowerCase().includes(query) || customer.phone.toLowerCase().includes(query),
    );
  }, [customerSearch, customers]);

  const selectedCustomer =
    draft.customer_mode === "existing"
      ? customers.find((customer) => customer.id === draft.customer_id)
      : draft.new_customer.name.trim()
        ? { name: draft.new_customer.name.trim(), phone: draft.new_customer.phone.trim() }
        : undefined;
  const selectedStaff = staff.find((member) => member.id === draft.staff_id);
  const selectedServices = services.filter((service) => draft.service_ids.includes(service.id));

  const updateDraft = (patch: Partial<BookingDraft>) => {
    setDraft((current) => {
      const next = { ...current, ...patch };
      if ("staff_id" in patch || "appointment_date" in patch || "service_ids" in patch) {
        next.start_time = "";
      }
      return next;
    });
    setStepError(null);
  };

  const goNext = () => {
    const result = validateBookingStep(step, draft);
    if (!result.success) {
      setStepError(result.error.issues[0]?.message ?? "Complete this step to continue");
      return;
    }

    if (step === "date" && draft.appointment_date < getTodayIsoDate()) {
      setStepError("Select today or a future date");
      return;
    }

    const next = getNextBookingStep(step);
    if (next) {
      setStep(next);
      setStepError(null);
    }
  };

  const goBack = () => {
    const previous = getPreviousBookingStep(step);
    if (previous) {
      setStep(previous);
      setStepError(null);
    }
  };

  const handleBook = async () => {
    const timeResult = validateBookingStep("time", draft);
    if (!timeResult.success) {
      setStepError(timeResult.error.issues[0]?.message ?? "Select an available time slot");
      return;
    }

    const slots = availabilityQuery.data?.slots ?? [];
    if (!isTimeSlotAvailable(draft.start_time, slots)) {
      setStepError("The selected time is no longer available. Choose another slot.");
      return;
    }

    try {
      await onSubmit(toBookingAppointmentCreatePayload(draft));
    } catch {
      // Parent handles toast/errors
    }
  };

  const isLastStep = step === "time";

  return (
    <div className="space-y-6">
      <BookingStepIndicator currentStep={step} />

      {step === "customer" ? (
        <CustomerStep
          mode={draft.customer_mode}
          customers={filteredCustomers}
          search={customerSearch}
          selectedId={draft.customer_id}
          newCustomer={draft.new_customer}
          onModeChange={(customer_mode) => {
            updateDraft({
              customer_mode,
              customer_id: "",
              new_customer: createEmptyNewCustomer(),
            });
          }}
          onSearchChange={setCustomerSearch}
          onSelect={(customerId) => updateDraft({ customer_id: customerId, customer_mode: "existing" })}
          onNewCustomerChange={(patch) =>
            updateDraft({
              customer_mode: "new",
              customer_id: "",
              new_customer: { ...draft.new_customer, ...patch },
            })
          }
        />
      ) : null}

      {step === "services" ? (
        <ServicesStep
          services={services}
          selectedIds={draft.service_ids}
          onToggle={(serviceId) => {
            const next = draft.service_ids.includes(serviceId)
              ? draft.service_ids.filter((id) => id !== serviceId)
              : [...draft.service_ids, serviceId];
            updateDraft({ service_ids: next });
          }}
          totalDuration={totalDuration}
        />
      ) : null}

      {step === "staff" ? (
        <StaffStep
          staff={staff}
          selectedId={draft.staff_id}
          onSelect={(staffId) => updateDraft({ staff_id: staffId })}
        />
      ) : null}

      {step === "date" ? (
        <DateStep
          value={draft.appointment_date}
          minDate={getTodayIsoDate()}
          onChange={(appointment_date) => updateDraft({ appointment_date })}
        />
      ) : null}

      {step === "time" ? (
        <TimeStep
          draft={draft}
          customer={selectedCustomer}
          staffMember={selectedStaff}
          selectedServices={selectedServices}
          totalDuration={totalDuration}
          availabilityQuery={availabilityQuery}
          onSelectTime={(start_time) => updateDraft({ start_time })}
          onNotesChange={(notes) => updateDraft({ notes })}
        />
      ) : null}

      {stepError ? <p className="text-sm text-destructive">{stepError}</p> : null}

      <div className="flex justify-between gap-2 border-t border-border pt-4">
        <Button type="button" variant="outline" disabled={loading} onClick={onCancel}>
          Cancel
        </Button>
        <div className="flex gap-2">
          {step !== "customer" ? (
            <Button type="button" variant="outline" disabled={loading} onClick={goBack}>
              <ArrowLeft className="h-4 w-4" />
              Back
            </Button>
          ) : null}
          {isLastStep ? (
            <Button type="button" disabled={loading || !draft.start_time} onClick={handleBook}>
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Booking
                </>
              ) : (
                <>
                  <Check className="h-4 w-4" />
                  Confirm booking
                </>
              )}
            </Button>
          ) : (
            <Button type="button" disabled={loading} onClick={goNext}>
              Next
              <ArrowRight className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

function CustomerStep({
  mode,
  customers,
  search,
  selectedId,
  newCustomer,
  onModeChange,
  onSearchChange,
  onSelect,
  onNewCustomerChange,
}: {
  mode: CustomerMode;
  customers: Customer[];
  search: string;
  selectedId: string;
  newCustomer: BookingDraft["new_customer"];
  onModeChange: (mode: CustomerMode) => void;
  onSearchChange: (value: string) => void;
  onSelect: (customerId: string) => void;
  onNewCustomerChange: (patch: Partial<BookingDraft["new_customer"]>) => void;
}) {
  const newCustomerErrors =
    mode === "new" ? bookingNewCustomerSchema.safeParse(newCustomer).error?.flatten().fieldErrors : undefined;

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-medium">Customer</h3>
        <p className="text-sm text-muted-foreground">Select an existing customer or register a walk-in.</p>
      </div>

      <div className="inline-flex rounded-lg border border-border p-1">
        <button
          type="button"
          onClick={() => onModeChange("existing")}
          className={cn(
            "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
            mode === "existing"
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:text-foreground",
          )}
        >
          Existing customer
        </button>
        <button
          type="button"
          onClick={() => onModeChange("new")}
          className={cn(
            "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
            mode === "new"
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:text-foreground",
          )}
        >
          New walk-in
        </button>
      </div>

      {mode === "existing" ? (
        <>
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={search}
              onChange={(event) => onSearchChange(event.target.value)}
              placeholder="Search by name or phone"
              className="pl-9"
            />
          </div>
          <div className="max-h-72 space-y-2 overflow-y-auto">
            {customers.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No customers match your search. Switch to New walk-in to register them.
              </p>
            ) : (
              customers.map((customer) => (
                <button
                  key={customer.id}
                  type="button"
                  onClick={() => onSelect(customer.id)}
                  className={cn(
                    "flex w-full items-center justify-between rounded-md border px-4 py-3 text-left text-sm transition-colors",
                    selectedId === customer.id
                      ? "border-primary bg-primary/5"
                      : "border-border hover:bg-muted/50",
                  )}
                >
                  <span>
                    <span className="font-medium">{customer.name}</span>
                    <span className="block text-muted-foreground">{customer.phone}</span>
                  </span>
                  {selectedId === customer.id ? <Check className="h-4 w-4 text-primary" /> : null}
                </button>
              ))
            )}
          </div>
        </>
      ) : (
        <div className="space-y-4 rounded-md border border-border p-4">
          <div className="space-y-2">
            <Label htmlFor="walkin_name">Name</Label>
            <Input
              id="walkin_name"
              value={newCustomer.name}
              onChange={(event) => onNewCustomerChange({ name: event.target.value })}
              placeholder="Full name"
            />
            {newCustomerErrors?.name?.[0] ? (
              <p className="text-sm text-destructive">{newCustomerErrors.name[0]}</p>
            ) : null}
          </div>
          <div className="space-y-2">
            <Label htmlFor="walkin_phone">Phone</Label>
            <Input
              id="walkin_phone"
              value={newCustomer.phone}
              onChange={(event) => onNewCustomerChange({ phone: event.target.value })}
              placeholder="10-digit mobile number"
              inputMode="numeric"
            />
            {newCustomerErrors?.phone?.[0] ? (
              <p className="text-sm text-destructive">{newCustomerErrors.phone[0]}</p>
            ) : null}
          </div>
          <div className="space-y-2">
            <Label htmlFor="walkin_email">Email (optional)</Label>
            <Input
              id="walkin_email"
              type="email"
              value={newCustomer.email ?? ""}
              onChange={(event) => onNewCustomerChange({ email: event.target.value })}
              placeholder="email@example.com"
            />
            {newCustomerErrors?.email?.[0] ? (
              <p className="text-sm text-destructive">{newCustomerErrors.email[0]}</p>
            ) : null}
          </div>
          <div className="space-y-2">
            <Label htmlFor="walkin_notes">Notes (optional)</Label>
            <Textarea
              id="walkin_notes"
              rows={2}
              value={newCustomer.notes ?? ""}
              onChange={(event) => onNewCustomerChange({ notes: event.target.value })}
              placeholder="Walk-in preferences or notes"
            />
          </div>
        </div>
      )}
    </div>
  );
}

function ServicesStep({
  services,
  selectedIds,
  onToggle,
  totalDuration,
}: {
  services: Service[];
  selectedIds: string[];
  onToggle: (serviceId: string) => void;
  totalDuration: number;
}) {
  const totalPrice = services
    .filter((service) => selectedIds.includes(service.id))
    .reduce((sum, service) => sum + Number.parseFloat(service.price), 0);

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-sm font-medium">Select services</h3>
          <p className="text-sm text-muted-foreground">Pick one or more services for this visit.</p>
        </div>
        {selectedIds.length > 0 ? (
          <p className="text-sm text-muted-foreground">
            {totalDuration} min · {formatCurrency(totalPrice)}
          </p>
        ) : null}
      </div>
      <div className="max-h-72 space-y-2 overflow-y-auto">
        {services.length === 0 ? (
          <p className="text-sm text-muted-foreground">No active services available.</p>
        ) : (
          services.map((service) => {
            const selected = selectedIds.includes(service.id);
            return (
              <button
                key={service.id}
                type="button"
                onClick={() => onToggle(service.id)}
                className={cn(
                  "flex w-full items-center justify-between rounded-md border px-4 py-3 text-left text-sm transition-colors",
                  selected ? "border-primary bg-primary/5" : "border-border hover:bg-muted/50",
                )}
              >
                <span>
                  <span className="font-medium">{service.name}</span>
                  <span className="block text-muted-foreground">
                    {service.category} · {service.duration_minutes} min · {formatCurrency(service.price)}
                  </span>
                </span>
                {selected ? <Check className="h-4 w-4 text-primary" /> : null}
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}

function StaffStep({
  staff,
  selectedId,
  onSelect,
}: {
  staff: StaffMember[];
  selectedId: string;
  onSelect: (staffId: string) => void;
}) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-medium">Select staff</h3>
        <p className="text-sm text-muted-foreground">Choose who will perform the services.</p>
      </div>
      <div className="max-h-72 space-y-2 overflow-y-auto">
        {staff.map((member) => (
          <button
            key={member.id}
            type="button"
            onClick={() => onSelect(member.id)}
            className={cn(
              "flex w-full items-center justify-between rounded-md border px-4 py-3 text-left text-sm transition-colors",
              selectedId === member.id ? "border-primary bg-primary/5" : "border-border hover:bg-muted/50",
            )}
          >
            <span>
              <span className="font-medium">{member.name}</span>
              <span className="block text-muted-foreground">{member.designation}</span>
            </span>
            {selectedId === member.id ? <Check className="h-4 w-4 text-primary" /> : null}
          </button>
        ))}
      </div>
    </div>
  );
}

function DateStep({
  value,
  minDate,
  onChange,
}: {
  value: string;
  minDate: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-medium">Select date</h3>
        <p className="text-sm text-muted-foreground">Pick the appointment date.</p>
      </div>
      <div className="space-y-2">
        <Label htmlFor="booking_date">Date</Label>
        <Input
          id="booking_date"
          type="date"
          min={minDate}
          value={value}
          onChange={(event) => onChange(event.target.value)}
        />
      </div>
    </div>
  );
}

function TimeStep({
  draft,
  customer,
  staffMember,
  selectedServices,
  totalDuration,
  availabilityQuery,
  onSelectTime,
  onNotesChange,
}: {
  draft: BookingDraft;
  customer?: Pick<Customer, "name" | "phone">;
  staffMember?: StaffMember;
  selectedServices: Service[];
  totalDuration: number;
  availabilityQuery: ReturnType<typeof useAvailability>;
  onSelectTime: (startTime: string) => void;
  onNotesChange: (notes: string) => void;
}) {
  const slots = availabilityQuery.data?.slots ?? [];

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-medium">Select time</h3>
        <p className="text-sm text-muted-foreground">
          Available slots for {formatShortDate(draft.appointment_date)} · {totalDuration} min total
        </p>
      </div>

      <div className="rounded-md border border-border bg-muted/30 p-4 text-sm">
        <dl className="grid gap-2 sm:grid-cols-2">
          <div>
            <dt className="text-muted-foreground">Customer</dt>
            <dd className="font-medium">{customer?.name ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Staff</dt>
            <dd className="font-medium">{staffMember?.name ?? "—"}</dd>
          </div>
          <div className="sm:col-span-2">
            <dt className="text-muted-foreground">Services</dt>
            <dd className="font-medium">{selectedServices.map((service) => service.name).join(", ") || "—"}</dd>
          </div>
        </dl>
      </div>

      {availabilityQuery.isLoading ? <LoadingSpinner label="Loading available slots" /> : null}

      {availabilityQuery.isError ? (
        <ErrorDisplay
          error={availabilityQuery.error}
          title="Unable to load availability"
          onRetry={() => availabilityQuery.refetch()}
        />
      ) : null}

      {!availabilityQuery.isLoading && !availabilityQuery.isError ? (
        slots.length === 0 ? (
          <p className="rounded-md border border-dashed border-border px-4 py-8 text-center text-sm text-muted-foreground">
            No available slots for this date. The staff member may not have working hours on this day,
            or all slots are booked. Try another date or staff member.
          </p>
        ) : (
          <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
            {slots.map((slot) => {
              const slotTime = toTimeInputValue(slot.start_time);
              const selected = draft.start_time === slotTime;
              return (
                <button
                  key={`${slot.start_time}-${slot.end_time}`}
                  type="button"
                  onClick={() => onSelectTime(slotTime)}
                  className={cn(
                    "rounded-md border px-3 py-2 text-sm font-medium transition-colors",
                    selected
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-border hover:bg-muted/50",
                  )}
                >
                  {formatTime(slot.start_time)}
                </button>
              );
            })}
          </div>
        )
      ) : null}

      <div className="space-y-2">
        <Label htmlFor="booking_notes">Notes (optional)</Label>
        <Textarea
          id="booking_notes"
          rows={3}
          value={draft.notes}
          onChange={(event) => onNotesChange(event.target.value)}
          placeholder="Any special requests or internal notes"
        />
      </div>
    </div>
  );
}

export { BOOKING_STEPS };
