import { cn } from "@/lib/utils";

interface SectionHeadingProps {
  eyebrow: string;
  title: string;
  description?: string;
  align?: "left" | "center";
  className?: string;
}

export function SectionHeading({
  eyebrow,
  title,
  description,
  align = "center",
  className,
}: SectionHeadingProps) {
  return (
    <div className={cn(align === "center" ? "mx-auto max-w-3xl text-center" : "max-w-2xl", className)}>
      <p className="text-[11px] font-medium uppercase tracking-luxury text-gold">{eyebrow}</p>
      <div className={cn("mt-5 h-px w-16 bg-gold", align === "center" && "mx-auto")} />
      <h2 className="mt-6 font-serif text-4xl leading-tight text-ivory sm:text-5xl lg:text-[3.5rem]">{title}</h2>
      {description ? <p className="mt-6 text-base leading-relaxed text-mist sm:text-lg">{description}</p> : null}
    </div>
  );
}
