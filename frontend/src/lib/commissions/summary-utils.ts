import type { Commission, MonthlyCommissionSummary } from "@/types/commissions";

export function getCurrentMonthKey() {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0");
  return `${year}-${month}`;
}

export function getMonthDateRange(monthKey: string) {
  const [year, month] = monthKey.split("-");
  const yearNum = Number.parseInt(year ?? "0", 10);
  const monthNum = Number.parseInt(month ?? "1", 10);
  const lastDay = new Date(yearNum, monthNum, 0).getDate();
  const monthPadded = String(monthNum).padStart(2, "0");

  return {
    start_date: `${yearNum}-${monthPadded}-01`,
    end_date: `${yearNum}-${monthPadded}-${String(lastDay).padStart(2, "0")}`,
  };
}

export function formatMonthLabel(monthKey: string) {
  const [year, month] = monthKey.split("-");
  const date = new Date(Number.parseInt(year ?? "0", 10), Number.parseInt(month ?? "1", 10) - 1, 1);
  return new Intl.DateTimeFormat("en-IN", { month: "long", year: "numeric" }).format(date);
}

export function isCommissionInMonth(commission: Commission, monthKey: string) {
  return commission.created_at.slice(0, 7) === monthKey;
}

export function summarizeCommissions(commissions: Commission[], monthKey: string): MonthlyCommissionSummary {
  const filtered = commissions.filter((item) => isCommissionInMonth(item, monthKey));

  return {
    month: monthKey,
    commissionTotal: filtered.reduce(
      (sum, item) => sum + Number.parseFloat(item.commission_amount),
      0,
    ),
    revenueTotal: filtered.reduce((sum, item) => sum + Number.parseFloat(item.service_revenue), 0),
    count: filtered.length,
  };
}
