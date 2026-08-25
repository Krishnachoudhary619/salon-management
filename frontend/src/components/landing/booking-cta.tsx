import { brand } from "@/lib/landing/content";

import { Reveal } from "./reveal";

export function BookingCta() {
  return (
    <section id="booking" className="scroll-mt-24 border-y border-gold/40 bg-ink-surface px-5 py-24 sm:px-8 lg:py-32">
      <Reveal>
        <div className="mx-auto max-w-3xl text-center">
          <p className="text-[11px] uppercase tracking-luxury text-gold">Reservations</p>
          <h2 className="mt-6 font-serif text-4xl text-ivory sm:text-5xl lg:text-6xl">
            Your next appointment is not on a waitlist.
          </h2>
          <p className="mt-6 text-base leading-relaxed text-mist sm:text-lg">
            Write to the desk, or telephone. We confirm within the hour during house hours — never by automated reply.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <a
              href="#contact"
              className="inline-flex w-full items-center justify-center bg-gold px-8 py-4 text-[11px] uppercase tracking-luxury text-ink transition-colors hover:bg-gold-light sm:w-auto"
            >
              Request a time
            </a>
            <a
              href={brand.whatsappHref}
              target="_blank"
              rel="noreferrer"
              className="inline-flex w-full items-center justify-center border border-white/25 px-8 py-4 text-[11px] uppercase tracking-luxury text-ivory transition-colors hover:border-gold hover:text-gold sm:w-auto"
            >
              WhatsApp the desk
            </a>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
