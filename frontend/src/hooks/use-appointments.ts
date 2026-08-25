"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "@/config/query-client";
import {
  cancelAppointment,
  createAppointment,
  fetchAppointment,
  fetchCalendarAppointments,
  fetchAppointments,
  rescheduleAppointment,
  updateAppointment,
} from "@/lib/api/appointments";
import type {
  AppointmentCalendarParams,
  AppointmentCreateRequest,
  AppointmentListParams,
  AppointmentRescheduleRequest,
  AppointmentUpdateRequest,
} from "@/types/appointments";

export function useAppointmentCalendar(params: AppointmentCalendarParams) {
  return useQuery({
    queryKey: queryKeys.appointments.calendar(params),
    queryFn: () => fetchCalendarAppointments(params),
    enabled: Boolean(params.start_date && params.end_date),
  });
}

export function useAppointment(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.appointments.detail(id ?? ""),
    queryFn: () => fetchAppointment(id!),
    enabled: Boolean(id),
  });
}

export function useAppointments(params: AppointmentListParams) {
  return useQuery({
    queryKey: queryKeys.appointments.list(params),
    queryFn: () => fetchAppointments(params),
  });
}

export function useAppointmentMutations() {
  const queryClient = useQueryClient();

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["appointments"] });
    queryClient.invalidateQueries({ queryKey: ["customers"] });
  };

  const createMutation = useMutation({
    mutationFn: (payload: AppointmentCreateRequest) => createAppointment(payload),
    onSuccess: invalidate,
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: AppointmentUpdateRequest }) =>
      updateAppointment(id, payload),
    onSuccess: invalidate,
  });

  const cancelMutation = useMutation({
    mutationFn: (id: string) => cancelAppointment(id),
    onSuccess: invalidate,
  });

  const rescheduleMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: AppointmentRescheduleRequest }) =>
      rescheduleAppointment(id, payload),
    onSuccess: invalidate,
  });

  return {
    createAppointment: createMutation.mutateAsync,
    updateAppointment: updateMutation.mutateAsync,
    cancelAppointment: cancelMutation.mutateAsync,
    rescheduleAppointment: rescheduleMutation.mutateAsync,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isCancelling: cancelMutation.isPending,
    isRescheduling: rescheduleMutation.isPending,
  };
}
