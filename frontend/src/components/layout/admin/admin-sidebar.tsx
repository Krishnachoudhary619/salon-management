"use client";

import { env } from "@/config/env";
import { useNavigation } from "@/hooks/use-navigation";
import { cn } from "@/lib/utils";

import { NavLink } from "./nav-link";

interface AdminSidebarProps {
  onNavigate?: () => void;
  className?: string;
}

export function AdminSidebar({ onNavigate, className }: AdminSidebarProps) {
  const { items } = useNavigation();

  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-30 hidden border-r border-border bg-card md:flex md:w-16 md:flex-col lg:w-64",
        className,
      )}
    >
      <div className="flex h-16 items-center border-b border-border px-3 lg:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary text-sm font-semibold text-primary-foreground">
            S
          </div>
          <div className="hidden min-w-0 lg:block">
            <p className="truncate text-sm font-semibold">{env.NEXT_PUBLIC_APP_NAME}</p>
            <p className="truncate text-xs text-muted-foreground">Admin</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto p-2 lg:p-3" aria-label="Main navigation">
        {items.map((item) => (
          <NavLink
            key={item.key}
            item={item}
            collapsed
            onNavigate={onNavigate}
          />
        ))}
      </nav>
    </aside>
  );
}
