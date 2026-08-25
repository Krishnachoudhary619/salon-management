"use client";

import Link from "next/link";
import { ChevronRight } from "lucide-react";

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
import { formatCurrency, formatDateTimeLabel } from "@/lib/format";
import type { Customer } from "@/types/customers";

interface CustomersTableProps {
  customers: Customer[];
  loading?: boolean;
}

export function CustomersTable({ customers, loading }: CustomersTableProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <Skeleton key={index} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (customers.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border py-12 text-center">
        <p className="text-sm font-medium">No customers found</p>
        <p className="mt-1 text-sm text-muted-foreground">Try a different search term.</p>
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Customer</TableHead>
          <TableHead>Phone</TableHead>
          <TableHead>Visits</TableHead>
          <TableHead>Total spent</TableHead>
          <TableHead>Last visit</TableHead>
          <TableHead className="text-right">Profile</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {customers.map((customer) => (
          <TableRow key={customer.id}>
            <TableCell>
              <div>
                <p className="font-medium">{customer.name}</p>
                {customer.email ? (
                  <p className="mt-0.5 text-xs text-muted-foreground">{customer.email}</p>
                ) : null}
              </div>
            </TableCell>
            <TableCell>{customer.phone}</TableCell>
            <TableCell>{customer.visit_count}</TableCell>
            <TableCell>{formatCurrency(customer.total_spent)}</TableCell>
            <TableCell>
              {customer.last_visit ? formatDateTimeLabel(customer.last_visit) : "—"}
            </TableCell>
            <TableCell className="text-right">
              <Button type="button" variant="ghost" size="sm" asChild>
                <Link href={`/customers/${customer.id}`}>
                  View
                  <ChevronRight className="h-4 w-4" />
                </Link>
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
