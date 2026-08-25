import Image from "next/image";

import { brand } from "@/lib/landing/content";

import { Reveal } from "./reveal";
import { SectionHeading } from "./section-heading";

export function About() {
  return (
    <section id="about" className="scroll-mt-24 bg-ink-surface px-5 py-24 sm:px-8 lg:py-32">
      <div className="mx-auto grid max-w-7xl items-center gap-14 lg:grid-cols-2 lg:gap-20">
        <Reveal>
          <div className="relative aspect-[4/5] overflow-hidden">
            <Image
              src="https://images.unsplash.com/photo-1521590832167-7bcbfaa6381f?auto=format&fit=crop&w=1400&q=80"
              alt="The Golden Premium atelier interior"
              fill
              className="object-cover"
            />
            <div className="absolute inset-0 ring-1 ring-inset ring-gold/30" />
          </div>
        </Reveal>

        <Reveal delay={0.12}>
          <SectionHeading
            align="left"
            eyebrow="The house story"
            title="A quieter kind of luxury"
            description="Founded for gentlemen and women who already have everything — except time, and a chair they can trust."
          />
          <div className="mt-8 space-y-5 text-base leading-relaxed text-mist">
            <p>
              {brand.name} opened above Gate Avenue as a refusal of the open-plan salon. We keep fewer chairs, longer
              appointments, and a staff who speak only when asked.
            </p>
            <p>
              The rooms are lined in dark stone and brass. The products are blended for Dubai heat. The guest book is
              not published. That is the entire point.
            </p>
          </div>
          <dl className="mt-10 grid grid-cols-2 gap-8 border-t border-white/10 pt-8">
            <div>
              <dt className="text-[11px] uppercase tracking-luxury text-gold">Established</dt>
              <dd className="mt-2 font-serif text-3xl text-ivory">2018</dd>
            </div>
            <div>
              <dt className="text-[11px] uppercase tracking-luxury text-gold">Private suites</dt>
              <dd className="mt-2 font-serif text-3xl text-ivory">Six</dd>
            </div>
          </dl>
        </Reveal>
      </div>
    </section>
  );
}
