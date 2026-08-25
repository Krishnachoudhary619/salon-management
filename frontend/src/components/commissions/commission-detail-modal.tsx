"use client";

import { Dialog } from "@/components/ui/dialog";
import { ErrorDisplay } from "@/components/feedback/error-display";
import { LoadingSpinner } from "@/components/feedback/loading-state";
import { useCommission } from "@/hooks/use-commissions";
import { formatCurrency, formatDateTimeLabel } from "@/lib/format";
import { formatCommission } from "@/lib/schemas/staff";
import type { Commission } from "@/types/commissions";

interface CommissionDetailModalProps {
  open: boolean;
  commissionId?: string;
  fallback?: Commission;
  onOpenChange: (open: boolean) => void;
}

function CommissionDetailContent({ commission }: { commission: Commission }) {
  return (
    <dl className="grid gap-4 text-sm sm:grid-cols-2">
      <div>
        <dt className="text-muted-foreground">Staff</dt>
        <dd className="font-medium">{commission.staff_name}</dd>
      </div>
      <div>
        <dt className="text-muted-foreground">Commission amount</dt>
        <dd className="text-lg font-semibold">{formatCurrency(commission.commission_amount)}</dd>
      </div>
      <div>
        <dt className="text-muted-foreground">Service revenue</dt>
        <dd className="font-medium">{formatCurrency(commission.service_revenue)}</dd>
      </div>
      <div>
        <dt className="text-muted-foreground">Commission rate</dt>
        <dd className="font-medium">{formatCommission(commission.commission_percentage)}</dd>
      </div>
      <div>
        <dt className="text-muted-foreground">Appointment</dt>
        <dd className="font-mono text-xs">{commission.appointment_id}</dd>
      </div>
      <div>
        <dt className="text-muted-foreground">Generated</dt>
        <dd className="font-medium">{formatDateTimeLabel(commission.created_at)}</dd>
      </div>
      <div className="sm:col-span-2">
        <dt className="text-muted-foreground">Last updated</dt>
        <dd className="font-medium">{formatDateTimeLabel(commission.updated_at)}</dd>
      </div>
    </dl>
  );
}

export function CommissionDetailModal({
  open,
  commissionId,
  fallback,
  onOpenChange,
}: CommissionDetailModalProps) {
  const commissionQuery = useCommission(commissionId);
  const commission = commissionQuery.data ?? fallback;

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Commission details"
      description="Historical commission snapshot. Rates are never recalculated."
      className="max-w-lg"
    >
      {commissionQuery.isLoading && !fallback ? <LoadingSpinner label="Loading commission" /> : null}
      {commissionQuery.isError && !fallback ? (
        <ErrorDisplay
          error={commissionQuery.error}
          title="Unable to load commission"
          onRetry={() => commissionQuery.refetch()}
        />
      ) : null}
      {commission ? <CommissionDetailContent commission={commission} /> : null}
    </Dialog>
  );
}
