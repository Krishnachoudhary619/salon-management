import { apiClient, apiRequest } from "@/lib/api/client";
import { apiEndpoints } from "@/config/routes";
import type { PaginatedData } from "@/types/api";
import type { Invoice, InvoiceListParams } from "@/types/invoices";

export async function fetchInvoices(params: InvoiceListParams = {}): Promise<PaginatedData<Invoice>> {
  return apiRequest(() => apiClient.get(apiEndpoints.invoices.list, { params }));
}

export async function fetchInvoice(id: string): Promise<Invoice> {
  return apiRequest(() => apiClient.get(apiEndpoints.invoices.detail(id)));
}

export async function fetchInvoiceByAppointment(appointmentId: string): Promise<Invoice | null> {
  const page = await fetchInvoices({ appointment_id: appointmentId, limit: 1 });
  return page.items[0] ?? null;
}
