export interface DashboardOverview {
  as_of: string;
  revenue_today: string;
  revenue_this_month: string;
  appointments_today: number;
  customers_served: number;
  average_ticket_size: string;
}

export interface RevenuePoint {
  period: string;
  revenue: string;
}

export interface RevenueSeries {
  group_by: string;
  start_date: string;
  end_date: string;
  items: RevenuePoint[];
}

export interface AppointmentDayPoint {
  appointment_date: string;
  total: number;
  completed: number;
  cancelled: number;
}

export interface AppointmentSeries {
  start_date: string;
  end_date: string;
  items: AppointmentDayPoint[];
}

export interface TopPerformer {
  staff_id: string;
  staff_name: string;
  revenue: string;
  appointments_completed: number;
}

export interface TopPerformers {
  start_date: string;
  end_date: string;
  items: TopPerformer[];
}

export interface DashboardRevenueParams {
  start_date?: string;
  end_date?: string;
  group_by?: "day" | "month";
}

export interface DashboardDateRangeParams {
  start_date?: string;
  end_date?: string;
}

export interface TopPerformersParams extends DashboardDateRangeParams {
  limit?: number;
}
