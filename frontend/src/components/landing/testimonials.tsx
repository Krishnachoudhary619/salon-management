import { testimonials } from "@/lib/landing/content";

import { Reveal } from "./reveal";
import { SectionHeading } from "./section-heading";

export function Testimonials() {
  return (
    <section id="testimonials" className="scroll-mt-24 bg-ink-surface px-5 py-24 sm:px-8 lg:py-32">
      <div className="mx-auto max-w-7xl">
        <Reveal>
          <SectionHeading
            eyebrow="From the book"
            title="Spoken, never advertised"
            description="We do not collect reviews. These notes were offered unprompted — and printed with permission."
          />
        </Reveal>

        <div className="mt-16 grid gap-10 lg:grid-cols-3">
          {testimonials.map((item, index) => (
            <Reveal key={item.name} delay={index * 0.08}>
              <blockquote className="flex h-full flex-col border border-white/10 p-8">
                <p className="font-serif text-2xl leading-snug text-ivory">“{item.quote}”</p>
                <footer className="mt-8 border-t border-white/10 pt-6">
                  <cite className="not-italic">
                    <span className="block text-sm text-ivory">{item.name}</span>
                  </cite>
                </footer>
              </blockquote>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
