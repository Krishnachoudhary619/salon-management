export interface StaffPerformanceMetrics {
  staff_id: string;
  staff_name: string;
  revenue_generated: string;
  customers_served: number;
  appointments_completed: number;
  tips_earned: string;
  commission_earned: string;
}

export interface TeamPerformanceResponse {
  start_date: string;
  end_date: string;
  items: StaffPerformanceMetrics[];
}

export interface StaffPerformanceResponse extends StaffPerformanceMetrics {
  start_date: string;
  end_date: string;
}

export interface PerformanceDateRangeParams {
  start_date?: string;
  end_date?: string;
}
