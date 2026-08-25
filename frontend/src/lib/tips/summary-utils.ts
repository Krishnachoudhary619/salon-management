import type { Tip, StaffTipSummary } from "@/types/tips";

export function getCurrentMonthKey() {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0");
  return `${year}-${month}`;
}

export function formatMonthLabel(monthKey: string) {
  const [year, month] = monthKey.split("-");
  const date = new Date(Number.parseInt(year ?? "0", 10), Number.parseInt(month ?? "1", 10) - 1, 1);
  return new Intl.DateTimeFormat("en-IN", { month: "long", year: "numeric" }).format(date);
}

export function isTipInMonth(tip: Tip, monthKey: string) {
  return tip.created_at.slice(0, 7) === monthKey;
}

export function summarizeTips(tips: Tip[], monthKey: string): StaffTipSummary {
  const filtered = tips.filter((item) => isTipInMonth(item, monthKey));
  return {
    month: monthKey,
    tipTotal: filtered.reduce((sum, item) => sum + Number.parseFloat(item.amount), 0),
    count: filtered.length,
  };
}
