import { z } from "zod";

import type { TipCreateRequest, TipUpdateRequest } from "@/types/tips";

export const tipFormSchema = z.object({
  appointment_id: z.string().min(1, "Select an appointment"),
  amount: z.coerce.number().positive("Amount must be greater than zero"),
  notes: z.string().max(5000, "Notes are too long").optional(),
});

export const tipEditSchema = z.object({
  amount: z.coerce.number().positive("Amount must be greater than zero"),
  notes: z.string().max(5000, "Notes are too long").optional(),
});

export type TipFormValues = z.infer<typeof tipFormSchema>;
export type TipEditValues = z.infer<typeof tipEditSchema>;

export function toTipCreatePayload(values: TipFormValues): TipCreateRequest {
  return {
    appointment_id: values.appointment_id,
    amount: values.amount,
    notes: values.notes?.trim() || null,
  };
}

export function toTipUpdatePayload(values: TipEditValues): TipUpdateRequest {
  return {
    amount: values.amount,
    notes: values.notes?.trim() || null,
  };
}

export function toTipEditValues(tip: { amount: string; notes: string | null }): TipEditValues {
  return {
    amount: Number.parseFloat(tip.amount),
    notes: tip.notes ?? "",
  };
}
