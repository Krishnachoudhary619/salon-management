import { z } from "zod";

import type { PaymentCreateRequest, PaymentMethod } from "@/types/payments";

export const PAYMENT_METHODS: PaymentMethod[] = ["CASH", "CARD", "UPI"];

export const paymentFormSchema = z.object({
  appointment_id: z.string().min(1, "Select an appointment"),
  amount: z.coerce.number().positive("Amount must be greater than zero"),
  payment_method: z.enum(["CASH", "CARD", "UPI"], {
    required_error: "Select a payment method",
  }),
});

export type PaymentFormValues = z.infer<typeof paymentFormSchema>;

export function toPaymentCreatePayload(values: PaymentFormValues): PaymentCreateRequest {
  return {
    appointment_id: values.appointment_id,
    amount: values.amount,
    payment_method: values.payment_method,
    payment_status: "SUCCESS",
  };
}

export function getRemainingBalance(total: string, paidAmount: string) {
  const remaining = Number.parseFloat(total) - Number.parseFloat(paidAmount);
  return remaining > 0 ? remaining : 0;
}
