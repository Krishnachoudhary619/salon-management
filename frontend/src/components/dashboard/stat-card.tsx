import type { LucideIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const TONES = {
  emerald: "bg-emerald-50 text-emerald-700",
  blue: "bg-sky-50 text-sky-700",
  amber: "bg-amber-50 text-amber-700",
  violet: "bg-violet-50 text-violet-700",
} as const;

interface StatCardProps {
  title: string;
  value: string;
  description?: string;
  icon: LucideIcon;
  loading?: boolean;
  tone?: keyof typeof TONES;
  className?: string;
}

export function StatCard({
  title,
  value,
  description,
  icon: Icon,
  loading,
  tone = "blue",
  className,
}: StatCardProps) {
  return (
    <Card
      className={cn(
        "overflow-hidden rounded-2xl border-border/70 shadow-none transition-shadow hover:shadow-md",
        className,
      )}
    >
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-3">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <span className={cn("flex h-10 w-10 items-center justify-center rounded-xl", TONES[tone])}>
            <Icon className="h-5 w-5" aria-hidden="true" />
          </span>
        </div>
        {loading ? (
          <Skeleton className="mt-4 h-9 w-28" />
        ) : (
          <p className="mt-4 text-3xl font-semibold tracking-tight">{value}</p>
        )}
        {description ? <p className="mt-1.5 text-xs text-muted-foreground">{description}</p> : null}
      </CardContent>
    </Card>
  );
}
