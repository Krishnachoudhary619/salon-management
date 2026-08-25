"use client";

import Image from "next/image";
import { motion } from "framer-motion";

import { brand } from "@/lib/landing/content";

export function Hero() {
  return (
    <section className="relative isolate min-h-[100svh] overflow-hidden">
      <Image
        src="https://images.unsplash.com/photo-1585747860715-2ba37e788b70?auto=format&fit=crop&w=2400&q=80"
        alt="Private grooming suite at Golden Premium Salon"
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
            <Image
              src={brand.logo}
              alt=""
              width={88}
              height={88}
              className="h-20 w-20 object-contain sm:h-24 sm:w-24"
              priority
            />
            <p className="text-[11px] uppercase tracking-luxury text-gold">DIFC · Dubai</p>
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
