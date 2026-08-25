"use client";

import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { brand } from "@/lib/landing/content";
import { createPublicBooking, fetchPublicAvailability, fetchPublicCatalog } from "@/lib/api/public-booking";
import { toApiTimeValue, toTimeInputValue } from "@/lib/appointments/calendar-utils";
import { getErrorMessage } from "@/lib/api/errors";
import { getTodayIsoDate } from "@/lib/schemas/booking-wizard";
import { formatCurrency, formatTime } from "@/lib/format";
import { toast } from "@/lib/toast";
import { cn } from "@/lib/utils";

import { Reveal } from "./reveal";
import { SectionHeading } from "./section-heading";

export function Contact() {
  const [submitting, setSubmitting] = useState(false);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [serviceId, setServiceId] = useState("");
  const [staffId, setStaffId] = useState("");
  const [date, setDate] = useState(getTodayIsoDate);
  const [startTime, setStartTime] = useState("");
  const [notes, setNotes] = useState("");

  const catalogQuery = useQuery({
    queryKey: ["public", "catalog"],
    queryFn: fetchPublicCatalog,
  });

  const selectedService = catalogQuery.data?.services.find((item) => item.id === serviceId);
  const duration = selectedService?.duration_minutes ?? 0;

  const availabilityParams =
    staffId && date && duration > 0
      ? { staff_id: staffId, date, duration_minutes: duration }
      : null;

  const availabilityQuery = useQuery({
    queryKey: ["public", "availability", availabilityParams],
    queryFn: () => fetchPublicAvailability(availabilityParams!),
    enabled: Boolean(availabilityParams),
  });

  const slots = availabilityQuery.data?.slots ?? [];

  useEffect(() => {
    setStartTime("");
  }, [staffId, date, serviceId]);

  const today = useMemo(() => getTodayIsoDate(), []);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const digits = phone.replace(/\D/g, "");
    if (digits.length < 10 || digits.length > 15) {
      toast.error("Enter a valid mobile number (10–15 digits).");
      return;
    }
    if (!serviceId || !staffId || !date || !startTime) {
      toast.error("Choose a service, stylist, date, and available time.");
      return;
    }

    setSubmitting(true);
    try {
      await createPublicBooking({
        name: name.trim(),
        phone: digits,
        staff_id: staffId,
        service_id: serviceId,
        appointment_date: date,
        start_time: toApiTimeValue(startTime),
        notes: notes.trim() || null,
      });
      setName("");
      setPhone("");
      setServiceId("");
      setStaffId("");
      setDate(getTodayIsoDate());
      setStartTime("");
      setNotes("");
      toast.success("Your chair is reserved. The desk will confirm shortly.");
    } catch (error) {
      toast.fromError(error, getErrorMessage(error, "Unable to reserve that time. Try another slot."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section id="contact" className="scroll-mt-24 bg-ink px-5 py-24 sm:px-8 lg:py-32">
      <div className="mx-auto grid max-w-7xl gap-16 lg:grid-cols-2">
        <Reveal>
          <SectionHeading
            align="left"
            eyebrow="The desk"
            title="Write, or call"
            description="Reservations are taken by name and appear immediately on the house calendar."
          />
          <dl className="mt-10 space-y-6 text-sm sm:text-base">
            <div>
              <dt className="text-[11px] uppercase tracking-luxury text-gold">Address</dt>
              <dd className="mt-2 text-mist">{brand.address}</dd>
            </div>
            <div>
              <dt className="text-[11px] uppercase tracking-luxury text-gold">Telephone</dt>
              <dd className="mt-2">
                <a href={brand.phoneHref} className="text-ivory transition-colors hover:text-gold">
                  {brand.phone}
                </a>
              </dd>
            </div>
            <div>
              <dt className="text-[11px] uppercase tracking-luxury text-gold">Email</dt>
              <dd className="mt-2">
                <a href={`mailto:${brand.email}`} className="text-ivory transition-colors hover:text-gold">
                  {brand.email}
                </a>
              </dd>
            </div>
            <div>
              <dt className="text-[11px] uppercase tracking-luxury text-gold">Hours</dt>
              <dd className="mt-2 text-mist">{brand.hours}</dd>
            </div>
          </dl>
        </Reveal>

        <Reveal delay={0.1}>
          <form onSubmit={handleSubmit} className="border border-white/10 bg-ink-surface p-6 sm:p-10" noValidate>
            <div className="grid gap-6 sm:grid-cols-2">
              <label className="block sm:col-span-2">
                <span className="text-[11px] uppercase tracking-luxury text-gold">Name</span>
                <input
                  required
                  name="name"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  className="mt-2 w-full border-b border-white/20 bg-transparent py-3 text-ivory outline-none transition-colors focus:border-gold"
                />
              </label>
              <label className="block">
                <span className="text-[11px] uppercase tracking-luxury text-gold">Telephone</span>
                <input
                  required
                  name="phone"
                  type="tel"
                  value={phone}
                  onChange={(event) => setPhone(event.target.value)}
                  placeholder="05XXXXXXXX"
                  className="mt-2 w-full border-b border-white/20 bg-transparent py-3 text-ivory outline-none transition-colors focus:border-gold"
                />
              </label>
              <label className="block">
                <span className="text-[11px] uppercase tracking-luxury text-gold">Preferred date</span>
                <input
                  required
                  name="date"
                  type="date"
                  min={today}
                  value={date}
                  onChange={(event) => setDate(event.target.value)}
                  className="mt-2 w-full border-b border-white/20 bg-transparent py-3 text-ivory outline-none transition-colors focus:border-gold [color-scheme:dark]"
                />
              </label>
              <label className="block sm:col-span-2">
                <span className="text-[11px] uppercase tracking-luxury text-gold">Service</span>
                <select
                  name="service"
                  required
                  value={serviceId}
                  onChange={(event) => setServiceId(event.target.value)}
                  className="mt-2 w-full border-b border-white/20 bg-ink-surface py-3 text-ivory outline-none transition-colors focus:border-gold"
                >
                  <option value="">
                    {catalogQuery.isLoading ? "Loading the menu…" : "Select a ritual"}
                  </option>
                  {(catalogQuery.data?.services ?? []).map((service) => (
                    <option key={service.id} value={service.id}>
                      {service.name} · {service.duration_minutes} min · {formatCurrency(service.price)}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block sm:col-span-2">
                <span className="text-[11px] uppercase tracking-luxury text-gold">Stylist</span>
                <select
                  name="staff"
                  required
                  value={staffId}
                  onChange={(event) => setStaffId(event.target.value)}
                  className="mt-2 w-full border-b border-white/20 bg-ink-surface py-3 text-ivory outline-none transition-colors focus:border-gold"
                >
                  <option value="">
                    {catalogQuery.isLoading ? "Loading stylists…" : "Select a stylist"}
                  </option>
                  {(catalogQuery.data?.staff ?? []).map((member) => (
                    <option key={member.id} value={member.id}>
                      {member.name} · {member.designation}
                    </option>
                  ))}
                </select>
              </label>

              <div className="sm:col-span-2">
                <p className="text-[11px] uppercase tracking-luxury text-gold">Available time</p>
                {!availabilityParams ? (
                  <p className="mt-3 text-sm text-mist">Choose a service, stylist, and date to see open chairs.</p>
                ) : availabilityQuery.isLoading ? (
                  <p className="mt-3 text-sm text-mist">Checking the book…</p>
                ) : availabilityQuery.isError ? (
                  <p className="mt-3 text-sm text-gold-light">
                    {getErrorMessage(availabilityQuery.error, "Unable to load times for this day.")}
                  </p>
                ) : slots.length === 0 ? (
                  <p className="mt-3 text-sm text-mist">
                    No open slots for this stylist on that date. Try another day or stylist.
                  </p>
                ) : (
                  <div className="mt-4 grid grid-cols-3 gap-2 sm:grid-cols-4">
                    {slots.map((slot) => {
                      const value = toTimeInputValue(slot.start_time);
                      const selected = startTime === value;
                      return (
                        <button
                          key={`${slot.start_time}-${slot.end_time}`}
                          type="button"
                          onClick={() => setStartTime(value)}
                          className={cn(
                            "border px-3 py-2 text-sm transition-colors",
                            selected
                              ? "border-gold bg-gold text-ink"
                              : "border-white/20 text-ivory hover:border-gold hover:text-gold",
                          )}
                        >
                          {formatTime(slot.start_time)}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>

              <label className="block sm:col-span-2">
                <span className="text-[11px] uppercase tracking-luxury text-gold">Note</span>
                <textarea
                  name="note"
                  rows={3}
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                  className="mt-2 w-full resize-none border-b border-white/20 bg-transparent py-3 text-ivory outline-none transition-colors focus:border-gold"
                  placeholder="Occasion, stylist preference, or house-call request"
                />
              </label>
            </div>
            <button
              type="submit"
              disabled={submitting || catalogQuery.isLoading}
              className="mt-10 w-full bg-gold py-4 text-[11px] uppercase tracking-luxury text-ink transition-colors hover:bg-gold-light disabled:opacity-60"
            >
              {submitting ? "Reserving" : "Reserve this chair"}
            </button>
          </form>
        </Reveal>
      </div>
    </section>
  );
}
