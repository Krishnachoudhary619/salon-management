"use client";

import { cn } from "@/lib/utils";
import { BOOKING_STEPS, type BookingStep } from "@/lib/schemas/booking-wizard";

const STEP_LABELS: Record<BookingStep, string> = {
  customer: "Customer",
  services: "Services",
  staff: "Staff",
  date: "Date",
  time: "Time",
};

interface BookingStepIndicatorProps {
  currentStep: BookingStep;
}

export function BookingStepIndicator({ currentStep }: BookingStepIndicatorProps) {
  const currentIndex = BOOKING_STEPS.indexOf(currentStep);

  return (
    <ol className="flex flex-wrap gap-2">
      {BOOKING_STEPS.map((step, index) => {
        const isComplete = index < currentIndex;
        const isCurrent = step === currentStep;

        return (
          <li
            key={step}
            className={cn(
              "flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium",
              isCurrent && "border-primary bg-primary text-primary-foreground",
              isComplete && !isCurrent && "border-primary/30 bg-primary/5 text-primary",
              !isCurrent && !isComplete && "border-border text-muted-foreground",
            )}
          >
            <span
              className={cn(
                "flex h-5 w-5 items-center justify-center rounded-full text-[10px]",
                isCurrent && "bg-primary-foreground text-primary",
                isComplete && !isCurrent && "bg-primary text-primary-foreground",
                !isCurrent && !isComplete && "bg-muted text-muted-foreground",
              )}
            >
              {index + 1}
            </span>
            {STEP_LABELS[step]}
          </li>
        );
      })}
    </ol>
  );
}
