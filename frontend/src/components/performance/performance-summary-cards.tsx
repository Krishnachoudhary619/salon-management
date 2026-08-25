"use client";

import { CalendarCheck, HandCoins, IndianRupee, Percent } from "lucide-react";

import { StatCard } from "@/components/dashboard/stat-card";
import { formatCurrency } from "@/lib/format";
import type { PerformanceTotals } from "@/lib/performance/summary-utils";

interface PerformanceSummaryCardsProps {
  totals: PerformanceTotals;
  loading?: boolean;
}

export function PerformanceSummaryCards({ totals, loading }: PerformanceSummaryCardsProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <StatCard
        title="Revenue Generated"
        value={formatCurrency(totals.revenue)}
        icon={IndianRupee}
        loading={loading}
      />
      <StatCard
        title="Appointments Completed"
        value={String(totals.appointments)}
        icon={CalendarCheck}
        loading={loading}
      />
      <StatCard
        title="Commission Earned"
        value={formatCurrency(totals.commission)}
        icon={Percent}
        loading={loading}
      />
      <StatCard
        title="Tips Earned"
        value={formatCurrency(totals.tips)}
        icon={HandCoins}
        loading={loading}
      />
    </div>
  );
}
