"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ChartCard } from "@/components/dashboard/chart-card";
import { formatChartDayLabel, formatCurrency } from "@/lib/format";
import type { RevenuePoint } from "@/types/dashboard";

interface RevenueTrendChartProps {
  items: RevenuePoint[];
  loading?: boolean;
}

export function RevenueTrendChart({ items, loading }: RevenueTrendChartProps) {
  const data = items.map((item) => ({
    label: formatChartDayLabel(item.period),
    revenue: Number.parseFloat(item.revenue),
  }));

  return (
    <ChartCard
      title="Revenue Trend"
      description="Daily revenue over the last 30 days"
      loading={loading}
      empty={!loading && data.length === 0}
    >
      <div className="h-[280px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-border" vertical={false} />
            <XAxis
              dataKey="label"
              tickLine={false}
              axisLine={false}
              minTickGap={24}
              tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
            />
            <YAxis
              tickLine={false}
              axisLine={false}
              width={56}
              tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
              tickFormatter={(value: number) => `₹${Math.round(value / 1000)}k`}
            />
            <Tooltip
              formatter={(value) => [formatCurrency(Number(value ?? 0)), "Revenue"]}
              labelClassName="text-foreground"
              contentStyle={{
                backgroundColor: "hsl(var(--popover))",
                borderColor: "hsl(var(--border))",
                borderRadius: "0.5rem",
              }}
            />
            <Line
              type="monotone"
              dataKey="revenue"
              stroke="hsl(var(--primary))"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </ChartCard>
  );
}
