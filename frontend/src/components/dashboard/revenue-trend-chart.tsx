"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
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
      title="Revenue"
      description="Daily takings over the last 30 days"
      loading={loading}
      empty={!loading && data.length === 0}
    >
      <div className="h-[280px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="revenueFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#0f766e" stopOpacity={0.22} />
                <stop offset="100%" stopColor="#0f766e" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="4 6" stroke="hsl(var(--border))" vertical={false} />
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
              tickFormatter={(value: number) =>
                value >= 1000 ? `SAR ${Math.round(value / 1000)}k` : `SAR ${Math.round(value)}`
              }
            />
            <Tooltip
              cursor={{ stroke: "#0f766e", strokeWidth: 1, strokeDasharray: "4 4" }}
              formatter={(value) => [formatCurrency(Number(value ?? 0)), "Revenue"]}
              labelClassName="text-foreground"
              contentStyle={{
                backgroundColor: "hsl(var(--popover))",
                borderColor: "hsl(var(--border))",
                borderRadius: "0.75rem",
                boxShadow: "0 8px 24px rgba(15, 23, 42, 0.08)",
              }}
            />
            <Area
              type="monotone"
              dataKey="revenue"
              stroke="#0f766e"
              strokeWidth={2.5}
              fill="url(#revenueFill)"
              dot={false}
              activeDot={{ r: 5, strokeWidth: 2, stroke: "#fff" }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </ChartCard>
  );
}
