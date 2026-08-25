"use client";

import { useMemo } from "react";

import { adminNavItems, type NavItem } from "@/config/navigation";
import { usePermissions } from "@/hooks/use-permissions";

function isNavItemVisible(
  item: NavItem,
  can: (permissions: NavItem["permissions"]) => boolean,
  canAny: (permissions: NavItem["permissions"]) => boolean,
) {
  if (item.anyPermission) {
    return canAny(item.permissions);
  }
  return can(item.permissions);
}

export function useNavigation() {
  const { can, canAny } = usePermissions();

  const items = useMemo(
    () => adminNavItems.filter((item) => isNavItemVisible(item, can, canAny)),
    [can, canAny],
  );

  return { items };
}
