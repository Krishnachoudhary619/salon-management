"use client";

import { cn } from "@/lib/utils";
import { REPORT_TYPE_LABELS } from "@/lib/reports/period-utils";
import type { ReportType } from "@/types/reports";

interface ReportTypeTabsProps {
  value: ReportType;
  onChange: (type: ReportType) => void;
  className?: string;
}

const REPORT_TYPES: ReportType[] = ["revenue", "appointments", "staff_performance"];

export function ReportTypeTabs({ value, onChange, className }: ReportTypeTabsProps) {
  return (
    <div className={cn("flex flex-wrap gap-2", className)}>
      {REPORT_TYPES.map((type) => (
        <button
          key={type}
          type="button"
          onClick={() => onChange(type)}
          className={cn(
            "rounded-md border px-4 py-2 text-sm font-medium transition-colors",
            value === type
              ? "border-primary bg-primary/5 text-primary"
              : "border-border text-muted-foreground hover:border-primary/40 hover:text-foreground",
          )}
        >
          {REPORT_TYPE_LABELS[type]}
        </button>
      ))}
    </div>
  );
}
