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
              src="/brand/house-story-image.jpeg"
              alt="Golden Premium Salon house story"
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
            description="Founded for gentlemen who already have everything — except time, and a chair they can trust."
          />
          <div className="mt-8 space-y-5 text-base leading-relaxed text-mist">
            <p>
              {brand.name} opened above Gate Avenue as a refusal of the open-plan salon. We keep fewer chairs, longer
              appointments, and a staff who speak only when asked.
            </p>
            <p>
              The rooms are lined in dark stone and brass. The products are blended for Saudi Arabia. The guest book is
              not published. That is the entire point.
            </p>
          </div>

        </Reveal>
      </div>
    </section>
  );
}
