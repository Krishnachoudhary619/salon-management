import { z } from "zod";

import type { StaffMember, StaffStatus } from "@/types/staff";

const phoneSchema = z
  .string()
  .trim()
  .regex(/^[0-9]{10,15}$/, "Phone must be 10-15 digits");

const statusSchema = z.enum(["ACTIVE", "INACTIVE", "ON_LEAVE"]);

const sharedFields = {
  name: z.string().trim().min(1, "Name is required").max(120, "Name is too long"),
  phone: phoneSchema,
  designation: z.string().trim().min(1, "Designation is required").max(80, "Designation is too long"),
  commission_percentage: z.coerce
    .number({ invalid_type_error: "Commission must be a number" })
    .min(0, "Commission cannot be negative")
    .max(100, "Commission cannot exceed 100"),
  joining_date: z.string().min(1, "Joining date is required"),
  status: statusSchema,
};

export const staffCreateFormSchema = z.object({
  ...sharedFields,
  email: z.string().trim().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required").max(72, "Password is too long"),
});

export const staffEditFormSchema = z.object(sharedFields);

export type StaffCreateFormValues = z.infer<typeof staffCreateFormSchema>;
export type StaffEditFormValues = z.infer<typeof staffEditFormSchema>;

export function toStaffCreatePayload(values: StaffCreateFormValues) {
  return {
    name: values.name,
    email: values.email,
    password: values.password,
    phone: values.phone,
    designation: values.designation,
    commission_percentage: values.commission_percentage,
    joining_date: values.joining_date,
    status: values.status,
  };
}

export function toStaffUpdatePayload(
  values: StaffEditFormValues,
  includeCommission: boolean,
): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    name: values.name,
    phone: values.phone,
    designation: values.designation,
    joining_date: values.joining_date,
    status: values.status,
  };

  if (includeCommission) {
    payload.commission_percentage = values.commission_percentage;
  }

  return payload;
}

export function toStaffEditFormValues(staff: StaffMember): StaffEditFormValues {
  return {
    name: staff.name,
    phone: staff.phone,
    designation: staff.designation,
    commission_percentage: Number.parseFloat(staff.commission_percentage),
    joining_date: staff.joining_date,
    status: staff.status,
  };
}

export function formatStaffStatus(status: StaffStatus) {
  return status
    .toLowerCase()
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function formatCommission(value: string | number) {
  const amount = typeof value === "string" ? Number.parseFloat(value) : value;
  if (Number.isNaN(amount)) {
    return "0%";
  }
  return `${amount % 1 === 0 ? amount.toFixed(0) : amount.toFixed(2)}%`;
}
