import { z } from "zod";

export const serviceFormSchema = z.object({
  name: z.string().trim().min(1, "Name is required").max(120, "Name is too long"),
  description: z.string().trim().max(2000, "Description is too long").optional(),
  category: z.string().trim().min(1, "Category is required").max(80, "Category is too long"),
  duration_minutes: z.coerce
    .number({ invalid_type_error: "Duration must be a number" })
    .int("Duration must be a whole number")
    .gt(0, "Duration must be greater than 0"),
  price: z.coerce
    .number({ invalid_type_error: "Price must be a number" })
    .gt(0, "Price must be greater than 0"),
  is_active: z.boolean(),
});

export type ServiceFormValues = z.infer<typeof serviceFormSchema>;

export function toServiceCreatePayload(values: ServiceFormValues) {
  return {
    name: values.name,
    description: values.description?.trim() || null,
    category: values.category,
    duration_minutes: values.duration_minutes,
    price: values.price,
    is_active: values.is_active,
  };
}

export function toServiceUpdatePayload(values: ServiceFormValues): Record<string, unknown> {
  return {
    name: values.name,
    description: values.description?.trim() || null,
    category: values.category,
    duration_minutes: values.duration_minutes,
    price: values.price,
    is_active: values.is_active,
  };
}

export function toServiceFormValues(service: {
  name: string;
  description: string | null;
  category: string;
  duration_minutes: number;
  price: string;
  is_active: boolean;
}): ServiceFormValues {
  return {
    name: service.name,
    description: service.description ?? "",
    category: service.category,
    duration_minutes: service.duration_minutes,
    price: Number.parseFloat(service.price),
    is_active: service.is_active,
  };
}
