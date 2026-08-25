"use client";

import Link from "next/link";
import { ArrowLeft, CalendarDays, IndianRupee, UserRound } from "lucide-react";

import { ErrorDisplay } from "@/components/feedback/error-display";
import { PageLoader } from "@/components/feedback/loading-state";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCustomer } from "@/hooks/use-customers";
import { formatCurrency, formatDateTimeLabel } from "@/lib/format";

interface CustomerProfileProps {
  customerId: string;
}

export function CustomerProfile({ customerId }: CustomerProfileProps) {
  const customerQuery = useCustomer(customerId);

  if (customerQuery.isLoading) {
    return <PageLoader label="Loading customer profile" />;
  }

  if (customerQuery.isError) {
    return (
      <ErrorDisplay
        error={customerQuery.error}
        title="Unable to load customer profile"
        onRetry={() => customerQuery.refetch()}
      />
    );
  }

  const customer = customerQuery.data;
  if (!customer) {
    return null;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-3">
          <Button type="button" variant="outline" size="sm" asChild>
            <Link href="/customers">
              <ArrowLeft className="h-4 w-4" />
              Back to customers
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">{customer.name}</h1>
            <p className="text-sm text-muted-foreground">Customer profile and visit summary</p>
          </div>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard
          title="Visit count"
          value={String(customer.visit_count)}
          icon={CalendarDays}
        />
        <StatCard
          title="Total spent"
          value={formatCurrency(customer.total_spent)}
          icon={IndianRupee}
        />
        <StatCard
          title="Last visit"
          value={customer.last_visit ? formatDateTimeLabel(customer.last_visit) : "No visits yet"}
          icon={UserRound}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Contact details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <DetailRow label="Phone" value={customer.phone} />
            <DetailRow label="Email" value={customer.email ?? "—"} />
            <DetailRow label="Customer since" value={formatDateTimeLabel(customer.created_at)} />
            <DetailRow label="Last updated" value={formatDateTimeLabel(customer.updated_at)} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              {customer.notes?.trim() ? customer.notes : "No notes recorded for this customer."}
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  icon: Icon,
}: {
  title: string;
  value: string;
  icon: typeof CalendarDays;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-bold tracking-tight">{value}</p>
      </CardContent>
    </Card>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
