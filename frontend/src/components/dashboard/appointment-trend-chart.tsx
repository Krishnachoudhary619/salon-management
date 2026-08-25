"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ChartCard } from "@/components/dashboard/chart-card";
import { formatChartDayLabel } from "@/lib/format";
import type { AppointmentDayPoint } from "@/types/dashboard";

interface AppointmentTrendChartProps {
  items: AppointmentDayPoint[];
  loading?: boolean;
}

export function AppointmentTrendChart({ items, loading }: AppointmentTrendChartProps) {
  const data = items.map((item) => ({
    label: formatChartDayLabel(item.appointment_date),
    total: item.total,
    completed: item.completed,
    cancelled: item.cancelled,
  }));

  return (
    <ChartCard
      title="Appointments"
      description="Daily volume over the last 30 days"
      loading={loading}
      empty={!loading && data.length === 0}
      action={
        <div className="hidden items-center gap-3 text-[11px] text-muted-foreground sm:flex">
          <span className="inline-flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-slate-800" /> Total
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-500" /> Done
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-rose-400" /> Cancelled
          </span>
        </div>
      }
    >
      <div className="h-[280px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }} barGap={2}>
            <CartesianGrid strokeDasharray="4 6" stroke="hsl(var(--border))" vertical={false} />
            <XAxis
              dataKey="label"
              tickLine={false}
              axisLine={false}
              minTickGap={24}
              tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
            />
            <YAxis
              allowDecimals={false}
              tickLine={false}
              axisLine={false}
              width={32}
              tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
            />
            <Tooltip
              cursor={{ fill: "hsl(var(--muted))", opacity: 0.45 }}
              contentStyle={{
                backgroundColor: "hsl(var(--popover))",
                borderColor: "hsl(var(--border))",
                borderRadius: "0.75rem",
                boxShadow: "0 8px 24px rgba(15, 23, 42, 0.08)",
              }}
            />
            <Bar dataKey="total" name="Total" fill="#1e293b" radius={[6, 6, 0, 0]} maxBarSize={18} />
            <Bar dataKey="completed" name="Completed" fill="#10b981" radius={[6, 6, 0, 0]} maxBarSize={18} />
            <Bar dataKey="cancelled" name="Cancelled" fill="#fb7185" radius={[6, 6, 0, 0]} maxBarSize={18} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartCard>
  );
}
