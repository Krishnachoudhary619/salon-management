import { services } from "@/lib/landing/content";

import { Reveal } from "./reveal";
import { SectionHeading } from "./section-heading";

export function Services() {
  return (
    <section id="services" className="scroll-mt-24 border-t border-white/10 bg-ink px-5 py-24 sm:px-8 lg:py-32">
      <div className="mx-auto max-w-7xl">
        <Reveal>
          <SectionHeading
            eyebrow="The menu"
            title="Services, without spectacle"
            description="A considered edit. Every ritual is timed, priced, and finished as if you were leaving for the opera."
          />
        </Reveal>

        <div className="mt-16 divide-y divide-white/10 border-y border-white/10">
          {services.map((service, index) => (
            <Reveal key={service.name} delay={index * 0.04}>
              <article className="grid gap-4 py-10 md:grid-cols-[1fr_auto] md:items-end">
                <div>
                  <div className="flex flex-wrap items-baseline gap-x-4 gap-y-2">
                    <h3 className="font-serif text-2xl text-ivory sm:text-3xl">{service.name}</h3>
                    <span className="text-[11px] uppercase tracking-luxury text-gold">{service.duration}</span>
                  </div>
                  <p className="mt-3 max-w-2xl text-sm leading-relaxed text-mist sm:text-base">{service.description}</p>
                </div>
                <p className="font-serif text-xl text-gold md:text-right">{service.price}</p>
              </article>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
