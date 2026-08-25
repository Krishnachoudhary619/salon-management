"use client";

import { LogOut, Menu } from "lucide-react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { toast } from "@/lib/toast";

import { UserProfileMenu } from "./user-profile-menu";

interface AdminHeaderProps {
  onMenuClick: () => void;
}

export function AdminHeader({ onMenuClick }: AdminHeaderProps) {
  const router = useRouter();
  const { logout, isLoading } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
      toast.success("Signed out successfully");
      router.replace("/login");
    } catch {
      toast.error("Unable to sign out. Please try again.");
    }
  };

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-border bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/80 md:px-6">
      <div className="flex items-center gap-3">
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="md:hidden"
          aria-label="Open navigation menu"
          aria-controls="admin-mobile-nav"
          onClick={onMenuClick}
        >
          <Menu className="h-5 w-5" />
        </Button>
        <div className="md:hidden">
          <p className="text-sm font-semibold">Salon Admin</p>
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        <UserProfileMenu />
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={isLoading}
          onClick={handleLogout}
          className="shrink-0"
        >
          <LogOut className="h-4 w-4" />
          <span className="hidden sm:inline">Logout</span>
        </Button>
      </div>
    </header>
  );
}
