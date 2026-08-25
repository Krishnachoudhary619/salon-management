export interface Commission {
  id: string;
  appointment_id: string;
  staff_id: string;
  staff_name: string;
  service_revenue: string;
  commission_percentage: string;
  commission_amount: string;
  created_at: string;
  updated_at: string;
}

export interface CommissionListParams {
  page?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  staff_id?: string;
  appointment_id?: string;
}

export interface MonthlyCommissionSummary {
  month: string;
  commissionTotal: number;
  revenueTotal: number;
  count: number;
}
