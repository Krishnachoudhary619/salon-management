import { z } from "zod";

export const customerFormSchema = z.object({
  name: z.string().trim().min(1, "Name is required").max(120, "Name is too long"),
  phone: z
    .string()
    .trim()
    .regex(/^[0-9]{10,15}$/, "Phone must be 10–15 digits"),
  email: z
    .string()
    .trim()
    .optional()
    .refine((value) => !value || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value), "Invalid email"),
  notes: z.string().trim().max(5000, "Notes are too long").optional(),
});

export type CustomerFormValues = z.infer<typeof customerFormSchema>;

export const bookingNewCustomerSchema = z.object({
  name: z.string().trim().min(1, "Name is required").max(120, "Name is too long"),
  phone: z
    .string()
    .trim()
    .regex(/^[0-9]{10,15}$/, "Phone must be 10–15 digits"),
  email: z
    .string()
    .trim()
    .optional()
    .refine((value) => !value || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value), "Invalid email"),
  notes: z.string().trim().max(5000, "Notes are too long").optional(),
});

export type BookingNewCustomerValues = z.infer<typeof bookingNewCustomerSchema>;

export function toCustomerCreatePayload(values: CustomerFormValues) {
  return {
    name: values.name.trim(),
    phone: values.phone.trim(),
    email: values.email?.trim() || null,
    notes: values.notes?.trim() || null,
  };
}

export function createEmptyNewCustomer(): BookingNewCustomerValues {
  return {
    name: "",
    phone: "",
    email: "",
    notes: "",
  };
}

export function toBookingCustomerPayload(values: BookingNewCustomerValues) {
  return {
    name: values.name.trim(),
    phone: values.phone.trim(),
    email: values.email?.trim() || null,
    notes: values.notes?.trim() || null,
  };
}
