"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ChartCard } from "@/components/dashboard/chart-card";
import { formatCurrency } from "@/lib/format";

interface EarningsChartPoint {
  name: string;
  revenue: number;
  commission: number;
  tips: number;
}

interface PerformanceEarningsChartProps {
  data: EarningsChartPoint[];
  loading?: boolean;
}

export function PerformanceEarningsChart({ data, loading }: PerformanceEarningsChartProps) {
  return (
    <ChartCard
      title="Earnings by staff"
      description="Revenue, commission, and tips per team member"
      loading={loading}
      empty={!loading && data.length === 0}
    >
      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-border" vertical={false} />
            <XAxis
              dataKey="name"
              tickLine={false}
              axisLine={false}
              minTickGap={16}
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
              formatter={(value, name) => [formatCurrency(Number(value ?? 0)), String(name)]}
              contentStyle={{
                backgroundColor: "hsl(var(--popover))",
                borderColor: "hsl(var(--border))",
                borderRadius: "0.5rem",
              }}
            />
            <Legend />
            <Bar dataKey="revenue" name="Revenue" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
            <Bar dataKey="commission" name="Commission" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            <Bar dataKey="tips" name="Tips" fill="#10b981" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartCard>
  );
}
