import type { AppointmentStatus } from "@/types/api";

export const APPOINTMENT_STATUS_COLORS: Record<
  AppointmentStatus,
  { bg: string; border: string; text: string; label: string }
> = {
  PENDING: { bg: "#e2e8f0", border: "#64748b", text: "#0f172a", label: "Pending" },
  CONFIRMED: { bg: "#dbeafe", border: "#2563eb", text: "#1e3a8a", label: "Confirmed" },
  ARRIVED: { bg: "#fef3c7", border: "#d97706", text: "#92400e", label: "Arrived" },
  IN_PROGRESS: { bg: "#ffedd5", border: "#ea580c", text: "#9a3412", label: "In progress" },
  COMPLETED: { bg: "#dcfce7", border: "#16a34a", text: "#166534", label: "Completed" },
  CANCELLED: { bg: "#fee2e2", border: "#dc2626", text: "#991b1b", label: "Cancelled" },
  NO_SHOW: { bg: "#fecaca", border: "#b91c1c", text: "#7f1d1d", label: "No show" },
};

export const RESCHEDULABLE_STATUSES: AppointmentStatus[] = [
  "PENDING",
  "CONFIRMED",
  "ARRIVED",
  "IN_PROGRESS",
];

export const TERMINAL_STATUSES: AppointmentStatus[] = ["COMPLETED", "CANCELLED", "NO_SHOW"];

export const CANCELLABLE_STATUSES: AppointmentStatus[] = ["PENDING", "CONFIRMED"];

export function canReschedule(status: AppointmentStatus) {
  return RESCHEDULABLE_STATUSES.includes(status);
}

export function canCancel(status: AppointmentStatus) {
  return CANCELLABLE_STATUSES.includes(status);
}

export function canConfirm(status: AppointmentStatus) {
  return status === "PENDING";
}

const NEXT_VISIT_STATUS: Partial<Record<AppointmentStatus, AppointmentStatus>> = {
  CONFIRMED: "ARRIVED",
  ARRIVED: "IN_PROGRESS",
  IN_PROGRESS: "COMPLETED",
};

const VISIT_ACTION_LABEL: Partial<Record<AppointmentStatus, string>> = {
  CONFIRMED: "Mark arrived",
  ARRIVED: "Start service",
  IN_PROGRESS: "Complete",
};

export function getNextVisitStatus(status: AppointmentStatus): AppointmentStatus | null {
  return NEXT_VISIT_STATUS[status] ?? null;
}

export function getVisitActionLabel(status: AppointmentStatus): string | null {
  return VISIT_ACTION_LABEL[status] ?? null;
}

export function canComplete(status: AppointmentStatus) {
  return status === "IN_PROGRESS";
}

export function canEdit(status: AppointmentStatus) {
  return !TERMINAL_STATUSES.includes(status);
}
