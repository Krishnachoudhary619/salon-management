"use client";

import Image from "next/image";
import { motion } from "framer-motion";

import { brand } from "@/lib/landing/content";

export function Hero() {
  return (
    <section className="relative isolate min-h-[100svh] overflow-hidden">
      <Image
        src="/brand/golden-salon-home-hero.png"
        alt="Golden Saloon storefront at night"
        fill
        priority
        className="object-cover"
      />
      <div className="absolute inset-0 bg-gradient-to-b from-ink/70 via-ink/55 to-ink" />

      <div className="relative mx-auto flex min-h-[100svh] max-w-7xl flex-col justify-end px-5 pb-20 pt-36 sm:px-8 lg:justify-center lg:pb-0">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
          className="max-w-3xl"
        >
          <div className="mb-8 flex items-center gap-4">
            <div className="relative flex h-[5.5rem] w-[5.5rem] shrink-0 items-center justify-center sm:h-[6.5rem] sm:w-[6.5rem]">
              <div
                aria-hidden
                className="absolute inset-[-18%] rounded-full bg-[radial-gradient(circle,rgba(212,175,55,0.42)_0%,rgba(212,175,55,0.14)_42%,transparent_72%)] blur-md"
              />
              <div
                aria-hidden
                className="absolute inset-0 rounded-full bg-gradient-to-br from-gold/35 via-gold/10 to-transparent opacity-90"
              />
              <div className="relative flex h-full w-full items-center justify-center overflow-hidden rounded-full border border-gold/35 bg-gradient-to-br from-gold/25 via-ink/50 to-ink/80 p-2.5 shadow-[0_0_32px_rgba(212,175,55,0.22)] sm:p-3">
                <Image
                  src={brand.logo}
                  alt=""
                  width={88}
                  height={88}
                  className="h-full w-full rounded-full object-cover"
                  priority
                />
              </div>
            </div>
            <p className="text-[11px] uppercase tracking-luxury text-gold">{brand.city} · Saudi Arabia</p>
          </div>
          <h1 className="font-serif text-5xl leading-[1.05] text-ivory sm:text-6xl lg:text-7xl">
            Grooming, composed
            <span className="block italic text-gold-light">for the few.</span>
          </h1>
          <p className="mt-8 max-w-xl text-base leading-relaxed text-mist sm:text-lg">
            {brand.tagline} A closed-door house for those who prefer silence, linen, and exacting hands.
          </p>
          <div className="mt-10 flex flex-col gap-4 sm:flex-row">
            <a
              href="#booking"
              className="inline-flex items-center justify-center bg-gold px-8 py-4 text-[11px] uppercase tracking-luxury text-ink transition-colors hover:bg-gold-light"
            >
              Reserve your chair
            </a>
            <a
              href="#services"
              className="inline-flex items-center justify-center border border-white/25 px-8 py-4 text-[11px] uppercase tracking-luxury text-ivory transition-colors hover:border-gold hover:text-gold"
            >
              View the menu
            </a>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
