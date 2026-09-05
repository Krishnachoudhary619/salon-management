"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchPublicCatalog } from "@/lib/api/public-booking";
import { formatCurrency } from "@/lib/format";

import { Reveal } from "./reveal";
import { SectionHeading } from "./section-heading";

export function Services() {
  const catalogQuery = useQuery({
    queryKey: ["public", "catalog"],
    queryFn: fetchPublicCatalog,
  });

  const services = catalogQuery.data?.services ?? [];

  return (
    <section id="services" className="scroll-mt-24 border-t border-white/10 bg-ink px-5 py-24 sm:px-8 lg:py-32">
      <div className="mx-auto max-w-7xl">
        <Reveal>
          <SectionHeading
            eyebrow="The menu"
            title="Services, without spectacle"
            description="A considered edit. Every ritual is priced and finished as if you were leaving for the opera."
          />
        </Reveal>

        <div className="mt-16 divide-y divide-white/10 border-y border-white/10">
          {catalogQuery.isLoading ? (
            <p className="py-10 text-sm text-mist">Loading the menu…</p>
          ) : catalogQuery.isError ? (
            <p className="py-10 text-sm text-gold-light">Unable to load services right now. Please try again shortly.</p>
          ) : services.length === 0 ? (
            <p className="py-10 text-sm text-mist">The menu will appear here once services are published.</p>
          ) : (
            services.map((service, index) => (
              <Reveal key={service.id} delay={index * 0.04}>
                <article className="grid gap-4 py-10 md:grid-cols-[1fr_auto] md:items-end">
                  <div>
                    <h3 className="font-serif text-2xl text-ivory sm:text-3xl">{service.name}</h3>
                    {service.category ? (
                      <p className="mt-3 max-w-2xl text-sm leading-relaxed text-mist sm:text-base">{service.category}</p>
                    ) : null}
                  </div>
                  <p className="font-display text-3xl font-medium tabular-nums tracking-wide text-gold md:text-right md:text-4xl">
                    {formatCurrency(service.price)}
                  </p>
                </article>
              </Reveal>
            ))
          )}
        </div>
      </div>
    </section>
  );
}
