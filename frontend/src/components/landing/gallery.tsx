import Image from "next/image";

import { gallery } from "@/lib/landing/content";

import { Reveal } from "./reveal";
import { SectionHeading } from "./section-heading";

export function Gallery() {
  return (
    <section id="gallery" className="scroll-mt-24 border-t border-white/10 bg-ink px-5 py-24 sm:px-8 lg:py-32">
      <div className="mx-auto max-w-7xl">
        <Reveal>
          <SectionHeading
            eyebrow="The atelier"
            title="Rooms kept for the evening"
            description="Stone, brass, and low light. Photography is permitted; social posting is not expected."
          />
        </Reveal>

        <div className="mt-16 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {gallery.map((item, index) => (
            <Reveal key={item.src} delay={index * 0.05} className={index === 0 ? "sm:col-span-2 lg:col-span-2" : undefined}>
              <figure className="relative aspect-[4/3] overflow-hidden lg:aspect-[5/4]">
                <Image src={item.src} alt={item.alt} fill className="object-cover transition duration-700 hover:scale-105" />
              </figure>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
