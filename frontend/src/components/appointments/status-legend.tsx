"use client";

import { APPOINTMENT_STATUS_COLORS } from "@/lib/appointments/status-colors";
import type { AppointmentStatus } from "@/types/api";

const STATUS_ORDER: AppointmentStatus[] = [
  "PENDING",
  "CONFIRMED",
  "ARRIVED",
  "IN_PROGRESS",
  "COMPLETED",
  "CANCELLED",
  "NO_SHOW",
];

export function StatusLegend() {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
      {STATUS_ORDER.map((status) => {
        const colors = APPOINTMENT_STATUS_COLORS[status];
        return (
          <div key={status} className="flex items-center gap-2 text-xs text-muted-foreground">
            <span
              className="inline-block h-3 w-3 rounded-sm border"
              style={{ backgroundColor: colors.bg, borderColor: colors.border }}
            />
            <span>{colors.label}</span>
          </div>
        );
      })}
    </div>
  );
}
