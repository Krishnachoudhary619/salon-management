export function toIsoDate(date: Date) {
  return date.toISOString().slice(0, 10);
}

export function getDateRange(days: number, endDate = new Date()) {
  const end = new Date(endDate);
  const start = new Date(end);
  start.setDate(end.getDate() - (days - 1));
  return {
    start_date: toIsoDate(start),
    end_date: toIsoDate(end),
  };
}

export function getMonthRange(months: number) {
  const end = new Date();
  const start = new Date(end.getFullYear(), end.getMonth() - (months - 1), 1);
  return {
    start_date: toIsoDate(start),
    end_date: toIsoDate(end),
  };
}

export function formatCurrency(value: string | number) {
  const amount = typeof value === "string" ? Number.parseFloat(value) : value;
  if (Number.isNaN(amount)) {
    return "SAR 0";
  }
  return new Intl.NumberFormat("en-SA", {
    style: "currency",
    currency: "SAR",
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatShortDate(value: string) {
  return new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "short",
  }).format(new Date(`${value}T00:00:00`));
}

export function formatTime(value: string) {
  const [hours, minutes] = value.split(":");
  const date = new Date();
  date.setHours(Number.parseInt(hours ?? "0", 10), Number.parseInt(minutes ?? "0", 10), 0, 0);
  return new Intl.DateTimeFormat("en-IN", {
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

export function formatDateTimeLabel(value: string) {
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function formatChartDayLabel(value: string) {
  return new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "short",
  }).format(new Date(`${value}T00:00:00`));
}

export function formatChartMonthLabel(value: string) {
  const [year, month] = value.split("-");
  const date = new Date(Number.parseInt(year ?? "0", 10), Number.parseInt(month ?? "1", 10) - 1, 1);
  return new Intl.DateTimeFormat("en-IN", {
    month: "short",
    year: "2-digit",
  }).format(date);
}

export function formatStatusLabel(status: string) {
  return status
    .toLowerCase()
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
