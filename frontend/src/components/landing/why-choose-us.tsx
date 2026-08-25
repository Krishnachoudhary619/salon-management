import { reasons } from "@/lib/landing/content";

import { Reveal } from "./reveal";
import { SectionHeading } from "./section-heading";

export function WhyChooseUs() {
  return (
    <section id="why-us" className="scroll-mt-24 bg-ink px-5 py-24 sm:px-8 lg:py-32">
      <div className="mx-auto max-w-7xl">
        <Reveal>
          <SectionHeading
            eyebrow="The house"
            title="Why the city keeps a chair here"
            description="Golden Premium is not a salon you wander into. It is a standing arrangement — for guests who treat appearance as part of their office."
          />
        </Reveal>

        <div className="mt-16 grid gap-px bg-white/10 sm:grid-cols-2">
          {reasons.map((reason, index) => (
            <Reveal key={reason.title} delay={index * 0.08} className="bg-ink-surface p-8 sm:p-10">
              <p className="font-serif text-2xl text-gold">{String(index + 1).padStart(2, "0")}</p>
              <h3 className="mt-6 font-serif text-2xl text-ivory">{reason.title}</h3>
              <p className="mt-4 text-sm leading-relaxed text-mist sm:text-base">{reason.copy}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
