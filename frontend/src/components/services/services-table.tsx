"use client";

import { Pencil, Trash2 } from "lucide-react";

import { PermissionGate } from "@/components/auth/permission-gate";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCurrency } from "@/lib/format";
import type { Service } from "@/types/services";

interface ServicesTableProps {
  services: Service[];
  loading?: boolean;
  onEdit: (service: Service) => void;
  onDeactivate: (service: Service) => void;
}

export function ServicesTable({ services, loading, onEdit, onDeactivate }: ServicesTableProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <Skeleton key={index} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (services.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border py-12 text-center">
        <p className="text-sm font-medium">No services found</p>
        <p className="mt-1 text-sm text-muted-foreground">Try adjusting your search or add a new service.</p>
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Category</TableHead>
          <TableHead>Duration</TableHead>
          <TableHead>Price</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {services.map((service) => (
          <TableRow key={service.id}>
            <TableCell>
              <div>
                <p className="font-medium">{service.name}</p>
                {service.description ? (
                  <p className="mt-0.5 line-clamp-1 text-xs text-muted-foreground">{service.description}</p>
                ) : null}
              </div>
            </TableCell>
            <TableCell>{service.category}</TableCell>
            <TableCell>{service.duration_minutes} min</TableCell>
            <TableCell>{formatCurrency(service.price)}</TableCell>
            <TableCell>
              <Badge variant={service.is_active ? "success" : "secondary"}>
                {service.is_active ? "Active" : "Inactive"}
              </Badge>
            </TableCell>
            <TableCell className="text-right">
              <div className="flex justify-end gap-1">
                <PermissionGate permissions={["services:write"]}>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    aria-label={`Edit ${service.name}`}
                    onClick={() => onEdit(service)}
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                </PermissionGate>
                <PermissionGate permissions={["services:delete"]}>
                  {service.is_active ? (
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      aria-label={`Deactivate ${service.name}`}
                      onClick={() => onDeactivate(service)}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  ) : null}
                </PermissionGate>
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
