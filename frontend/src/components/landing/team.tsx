import Image from "next/image";

import { team } from "@/lib/landing/content";

import { Reveal } from "./reveal";
import { SectionHeading } from "./section-heading";

export function Team() {
  return (
    <section id="team" className="scroll-mt-24 bg-ink px-5 py-24 sm:px-8 lg:py-32">
      <div className="mx-auto max-w-7xl">
        <Reveal>
          <SectionHeading
            eyebrow="The masters"
            title="Hands you do not rush"
            description="Each stylist keeps a closed book. Introductions are made once; loyalty is assumed thereafter."
          />
        </Reveal>

        <div className="mt-16 grid gap-10 sm:grid-cols-2 lg:grid-cols-3">
          {team.map((member, index) => (
            <Reveal key={member.name} delay={index * 0.08}>
              <article>
                <div className="relative aspect-[3/4] overflow-hidden">
                  <Image src={member.image} alt={member.name} fill className="object-cover" />
                  <div className="absolute inset-0 bg-gradient-to-t from-ink via-transparent to-transparent" />
                </div>
                <p className="mt-5 text-[11px] uppercase tracking-luxury text-gold">{member.role}</p>
                <h3 className="mt-2 font-serif text-2xl text-ivory">{member.name}</h3>
                <p className="mt-3 text-sm leading-relaxed text-mist">{member.bio}</p>
              </article>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
