"use client";

import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@/config/query-client";
import { fetchInvoice, fetchInvoiceByAppointment, fetchInvoices } from "@/lib/api/invoices";
import type { InvoiceListParams } from "@/types/invoices";

export function useInvoices(params: InvoiceListParams) {
  return useQuery({
    queryKey: queryKeys.invoices.list(params),
    queryFn: () => fetchInvoices(params),
  });
}

export function useInvoice(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.invoices.detail(id ?? ""),
    queryFn: () => fetchInvoice(id!),
    enabled: Boolean(id),
  });
}

export function useInvoiceByAppointment(appointmentId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.invoices.byAppointment(appointmentId ?? ""),
    queryFn: () => fetchInvoiceByAppointment(appointmentId!),
    enabled: Boolean(appointmentId),
  });
}
