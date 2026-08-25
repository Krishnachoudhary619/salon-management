import { QueryClient, isServer } from "@tanstack/react-query";

import { ApiError } from "@/lib/api/errors";
import type {
  DashboardDateRangeParams,
  DashboardRevenueParams,
  TopPerformersParams,
} from "@/types/dashboard";
import type { ServiceListParams } from "@/types/services";
import type { StaffListParams } from "@/types/staff";
import type { CustomerListParams } from "@/types/customers";
import type { AppointmentCalendarParams, AppointmentListParams } from "@/types/appointments";
import type { AvailabilityParams } from "@/types/availability";
import type { CommissionListParams } from "@/types/commissions";
import type { InvoiceListParams } from "@/types/invoices";
import type { PaymentListParams } from "@/types/payments";
import type { PerformanceDateRangeParams } from "@/types/performance";
import type { TaskListParams } from "@/types/tasks";
import type { TipListParams } from "@/types/tips";

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000,
        gcTime: 5 * 60 * 1000,
        retry: (failureCount, error) => {
          if (error instanceof ApiError && error.status === 401) {
            return false;
          }
          return failureCount < 2;
        },
        refetchOnWindowFocus: false,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

let browserQueryClient: QueryClient | undefined;

export function getQueryClient() {
  if (isServer) {
    return makeQueryClient();
  }
  if (!browserQueryClient) {
    browserQueryClient = makeQueryClient();
  }
  return browserQueryClient;
}

export const queryKeys = {
  auth: {
    me: ["auth", "me"] as const,
  },
  dashboard: {
    overview: ["dashboard", "overview"] as const,
    revenue: (params: DashboardRevenueParams) => ["dashboard", "revenue", params] as const,
    appointments: (params: DashboardDateRangeParams) => ["dashboard", "appointments", params] as const,
    topPerformers: (params: TopPerformersParams) => ["dashboard", "top-performers", params] as const,
    upcomingAppointments: (limit: number) => ["dashboard", "upcoming-appointments", limit] as const,
  },
  services: {
    list: (params: ServiceListParams) => ["services", "list", params] as const,
  },
  staff: {
    list: (params: StaffListParams) => ["staff", "list", params] as const,
  },
  customers: {
    list: (params: CustomerListParams) => ["customers", "list", params] as const,
    detail: (id: string) => ["customers", "detail", id] as const,
  },
  appointments: {
    calendar: (params: AppointmentCalendarParams) => ["appointments", "calendar", params] as const,
    detail: (id: string) => ["appointments", "detail", id] as const,
    list: (params: AppointmentListParams) => ["appointments", "list", params] as const,
  },
  availability: {
    detail: (params: AvailabilityParams | null) => ["availability", params] as const,
  },
  payments: {
    list: (params: PaymentListParams) => ["payments", "list", params] as const,
  },
  invoices: {
    list: (params: InvoiceListParams) => ["invoices", "list", params] as const,
    detail: (id: string) => ["invoices", "detail", id] as const,
    byAppointment: (appointmentId: string) => ["invoices", "appointment", appointmentId] as const,
  },
  commissions: {
    list: (params: CommissionListParams) => ["commissions", "list", params] as const,
    detail: (id: string) => ["commissions", "detail", id] as const,
    byStaff: (staffId: string, params: Omit<CommissionListParams, "staff_id">) =>
      ["commissions", "staff", staffId, params] as const,
  },
  performance: {
    team: (params: PerformanceDateRangeParams) => ["performance", "team", params] as const,
    staff: (staffId: string, params: PerformanceDateRangeParams) =>
      ["performance", "staff", staffId, params] as const,
  },
  tips: {
    list: (params: TipListParams) => ["tips", "list", params] as const,
    detail: (id: string) => ["tips", "detail", id] as const,
  },
  tasks: {
    list: (params: TaskListParams) => ["tasks", "list", params] as const,
    detail: (id: string) => ["tasks", "detail", id] as const,
  },
} as const;
