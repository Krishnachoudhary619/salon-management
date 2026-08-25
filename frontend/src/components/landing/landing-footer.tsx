import Image from "next/image";
import Link from "next/link";

import { brand, navLinks } from "@/lib/landing/content";

export function LandingFooter() {
  return (
    <footer className="border-t border-white/10 bg-ink px-5 py-16 sm:px-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-12 lg:flex-row lg:items-start lg:justify-between">
        <div className="max-w-sm">
          <div className="flex items-center gap-3">
            <Image src={brand.logo} alt="" width={56} height={56} className="h-14 w-14 object-contain" />
            <p className="font-serif text-xl text-ivory">{brand.name}</p>
          </div>
          <p className="mt-5 text-sm leading-relaxed text-mist">{brand.tagline}</p>
        </div>

        <nav className="grid grid-cols-2 gap-x-10 gap-y-3 text-[11px] uppercase tracking-[0.2em] text-mist">
          {navLinks.map((link) => (
            <a key={link.href} href={link.href} className="hover:text-gold">
              {link.label}
            </a>
          ))}
        </nav>

        <div className="text-sm text-mist">
          <p>{brand.address}</p>
          <p className="mt-2">{brand.hours}</p>
          <Link href="/login" className="mt-6 inline-block text-[11px] uppercase tracking-luxury text-white/40 hover:text-gold">
            House staff
          </Link>
        </div>
      </div>
      <p className="mx-auto mt-16 max-w-7xl border-t border-white/10 pt-8 text-[11px] uppercase tracking-luxury text-white/35">
        © {new Date().getFullYear()} {brand.name}. Dubai.
      </p>
    </footer>
  );
}
