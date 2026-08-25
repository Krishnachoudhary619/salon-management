export const apiEndpoints = {
  auth: {
    login: "/auth/login",
    logout: "/auth/logout",
    refresh: "/auth/refresh-token",
    me: "/auth/me",
  },
  dashboard: {
    overview: "/dashboard/overview",
    revenue: "/dashboard/revenue",
    appointments: "/dashboard/appointments",
    topPerformers: "/dashboard/top-performers",
  },
  appointments: {
    list: "/appointments",
    calendar: "/appointments/calendar",
    detail: (id: string) => `/appointments/${id}`,
    cancel: (id: string) => `/appointments/${id}/cancel`,
    reschedule: (id: string) => `/appointments/${id}/reschedule`,
  },
  services: {
    list: "/services",
    detail: (id: string) => `/services/${id}`,
  },
  staff: {
    list: "/staff",
    detail: (id: string) => `/staff/${id}`,
  },
  customers: {
    list: "/customers",
    detail: (id: string) => `/customers/${id}`,
  },
  availability: {
    list: "/availability",
  },
  payments: {
    list: "/payments",
  },
  invoices: {
    list: "/invoices",
    detail: (id: string) => `/invoices/${id}`,
  },
  commissions: {
    list: "/commissions",
    detail: (id: string) => `/commissions/${id}`,
    byStaff: (staffId: string) => `/commissions/staff/${staffId}`,
  },
  performance: {
    team: "/performance/team",
    staff: (staffId: string) => `/performance/staff/${staffId}`,
  },
  tips: {
    list: "/tips",
    detail: (id: string) => `/tips/${id}`,
    byStaff: (staffId: string) => `/tips/staff/${staffId}`,
  },
  tasks: {
    list: "/tasks",
    detail: (id: string) => `/tasks/${id}`,
  },
} as const;

export const publicRoutes = ["/login"] as const;

export { appRoutes, adminNavItems } from "@/config/navigation";

export const defaultAuthenticatedRoute = "/";

export const roleHomeRoutes = {
  ADMIN: "/",
  RECEPTIONIST: "/appointments",
  STAFF: "/appointments",
} as const;
