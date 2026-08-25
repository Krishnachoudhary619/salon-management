import { AdminLayout } from "@/components/layout/admin";
import { PermissionRouteGuard, RouteGuard } from "@/components/auth";

export default function AdminRouteLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <RouteGuard>
      <PermissionRouteGuard>
        <AdminLayout>{children}</AdminLayout>
      </PermissionRouteGuard>
    </RouteGuard>
  );
}
