import {
  BarChart3,
  Calendar,
  CheckSquare,
  CreditCard,
  HandCoins,
  LayoutDashboard,
  Percent,
  Scissors,
  TrendingUp,
  UserCog,
  Users,
  type LucideIcon,
} from "lucide-react";

import type { Permission } from "@/types/api";

export const appRoutes = {
  dashboard: "/",
  appointments: "/appointments",
  customers: "/customers",
  services: "/services",
  staff: "/staff",
  payments: "/payments",
  commissions: "/commissions",
  tips: "/tips",
  tasks: "/tasks",
  reports: "/reports",
  performance: "/performance",
} as const;

export type AppRouteKey = keyof typeof appRoutes;

export interface NavItem {
  key: AppRouteKey;
  title: string;
  href: string;
  icon: LucideIcon;
  permissions: Permission[];
  anyPermission?: boolean;
}

export const adminNavItems: NavItem[] = [
  {
    key: "dashboard",
    title: "Dashboard",
    href: appRoutes.dashboard,
    icon: LayoutDashboard,
    permissions: ["dashboard:read"],
  },
  {
    key: "appointments",
    title: "Appointments",
    href: appRoutes.appointments,
    icon: Calendar,
    permissions: ["appointments:read", "appointments:read_own"],
    anyPermission: true,
  },
  {
    key: "customers",
    title: "Customers",
    href: appRoutes.customers,
    icon: Users,
    permissions: ["customers:read"],
  },
  {
    key: "services",
    title: "Services",
    href: appRoutes.services,
    icon: Scissors,
    permissions: ["services:read"],
  },
  {
    key: "staff",
    title: "Staff",
    href: appRoutes.staff,
    icon: UserCog,
    permissions: ["staff:read"],
  },
  {
    key: "payments",
    title: "Payments",
    href: appRoutes.payments,
    icon: CreditCard,
    permissions: ["payments:read"],
  },
  {
    key: "commissions",
    title: "Commissions",
    href: appRoutes.commissions,
    icon: Percent,
    permissions: ["commissions:read", "commissions:read_own"],
    anyPermission: true,
  },
  {
    key: "tips",
    title: "Tips",
    href: appRoutes.tips,
    icon: HandCoins,
    permissions: ["tips:read", "tips:read_own"],
    anyPermission: true,
  },
  {
    key: "tasks",
    title: "Tasks",
    href: appRoutes.tasks,
    icon: CheckSquare,
    permissions: ["tasks:read", "tasks:read_own"],
    anyPermission: true,
  },
  {
    key: "performance",
    title: "Performance",
    href: appRoutes.performance,
    icon: TrendingUp,
    permissions: ["performance:read", "performance:read_own"],
    anyPermission: true,
  },
  {
    key: "reports",
    title: "Reports",
    href: appRoutes.reports,
    icon: BarChart3,
    permissions: ["reports:read"],
  },
];
