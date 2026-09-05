import Image from "next/image";

import { gallery } from "@/lib/landing/content";

import { Reveal } from "./reveal";
import { SectionHeading } from "./section-heading";

export function Gallery() {
  const [hero, ...row] = gallery.slice(0, 4);

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

        <div className="mt-16 flex flex-col gap-4">
          <Reveal>
            <figure className="relative aspect-[16/9] overflow-hidden sm:aspect-[21/9]">
              <Image
                src={hero.src}
                alt={hero.alt}
                fill
                priority
                className="object-cover transition duration-700 hover:scale-[1.02]"
              />
            </figure>
          </Reveal>

          <div className="grid gap-4 sm:grid-cols-3">
            {row.map((item, index) => (
              <Reveal key={item.src} delay={(index + 1) * 0.05}>
                <figure className="relative aspect-[4/3] overflow-hidden">
                  <Image
                    src={item.src}
                    alt={item.alt}
                    fill
                    className="object-cover transition duration-700 hover:scale-105"
                  />
                </figure>
              </Reveal>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
