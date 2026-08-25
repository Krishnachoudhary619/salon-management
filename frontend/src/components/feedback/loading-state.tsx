"use client";

import { Loader2 } from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface LoadingStateProps {
  label?: string;
  className?: string;
}

export function LoadingSpinner({ label = "Loading", className }: LoadingStateProps) {
  return (
    <div className={cn("flex items-center justify-center gap-2 text-sm text-muted-foreground", className)}>
      <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

export function PageLoader({ label = "Loading" }: LoadingStateProps) {
  return (
    <div className="flex min-h-[40vh] items-center justify-center">
      <LoadingSpinner label={label} />
    </div>
  );
}

export function FullPageLoader({ label = "Loading application" }: LoadingStateProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <LoadingSpinner label={label} />
    </div>
  );
}

interface LoadingStatePropsExtended extends LoadingStateProps {
  rows?: number;
}

export function LoadingState({ label = "Loading", rows = 3, className }: LoadingStatePropsExtended) {
  return (
    <div className={cn("space-y-3", className)} aria-busy="true" aria-label={label}>
      {Array.from({ length: rows }).map((_, index) => (
        <Skeleton key={index} className="h-10 w-full" />
      ))}
    </div>
  );
}
