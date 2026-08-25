"use client";

import { cn } from "@/lib/utils";
import { REPORT_PERIOD_LABELS } from "@/lib/reports/period-utils";
import type { ReportPeriod } from "@/types/reports";

interface ReportPeriodFilterProps {
  value: ReportPeriod;
  onChange: (period: ReportPeriod) => void;
  className?: string;
}

const PERIODS: ReportPeriod[] = ["daily", "weekly", "monthly"];

export function ReportPeriodFilter({ value, onChange, className }: ReportPeriodFilterProps) {
  return (
    <div className={cn("inline-flex rounded-lg border border-border p-1", className)}>
      {PERIODS.map((period) => (
        <button
          key={period}
          type="button"
          onClick={() => onChange(period)}
          className={cn(
            "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
            value === period
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:text-foreground",
          )}
        >
          {REPORT_PERIOD_LABELS[period]}
        </button>
      ))}
    </div>
  );
}
