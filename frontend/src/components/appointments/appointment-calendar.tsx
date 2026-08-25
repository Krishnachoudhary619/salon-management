"use client";

import { useMemo } from "react";
import FullCalendar from "@fullcalendar/react";
import classicThemePlugin from "@fullcalendar/react/themes/classic";
import dayGridPlugin from "@fullcalendar/react/daygrid";
import timeGridPlugin from "@fullcalendar/react/timegrid";
import interactionPlugin from "@fullcalendar/react/interaction";
import type {
  DateClickInfo,
  DatesSetInfo,
  EventClickInfo,
  EventDropInfo,
} from "@fullcalendar/react";

import "@fullcalendar/react/skeleton.css";
import "@fullcalendar/react/themes/classic/theme.css";
import "@fullcalendar/react/themes/classic/palette.css";

import { appointmentToEvent, getCalendarRange } from "@/lib/appointments/calendar-utils";
import { canReschedule } from "@/lib/appointments/status-colors";
import type { Appointment } from "@/types/api";
import type { AppointmentCalendarParams } from "@/types/appointments";

interface AppointmentCalendarProps {
  appointments: Appointment[];
  loading?: boolean;
  editable?: boolean;
  onRangeChange: (params: AppointmentCalendarParams) => void;
  onDateClick: (info: DateClickInfo) => void;
  onEventClick: (appointment: Appointment) => void;
  onEventDrop?: (appointment: Appointment, info: EventDropInfo) => Promise<void>;
}

export function AppointmentCalendar({
  appointments,
  loading,
  editable = false,
  onRangeChange,
  onDateClick,
  onEventClick,
  onEventDrop,
}: AppointmentCalendarProps) {
  const events = useMemo(() => appointments.map(appointmentToEvent), [appointments]);

  const handleDatesSet = (info: DatesSetInfo) => {
    const range = getCalendarRange(info.start, info.end);
    onRangeChange(range);
  };

  const handleEventClick = (info: EventClickInfo) => {
    const appointment = info.event.extendedProps.appointment as Appointment | undefined;
    if (appointment) {
      onEventClick(appointment);
    }
  };

  const handleEventDrop = async (info: EventDropInfo) => {
    const appointment = info.event.extendedProps.appointment as Appointment | undefined;
    if (!appointment || !onEventDrop || !canReschedule(appointment.status)) {
      info.revert();
      return;
    }

    try {
      await onEventDrop(appointment, info);
    } catch {
      info.revert();
    }
  };

  return (
    <div className="appointment-calendar relative">
      {loading ? (
        <div className="absolute inset-x-0 top-0 z-10 flex justify-center py-2">
          <span className="rounded-full bg-background/90 px-3 py-1 text-xs text-muted-foreground shadow-sm">
            Updating calendar…
          </span>
        </div>
      ) : null}
      <FullCalendar
        plugins={[classicThemePlugin, dayGridPlugin, timeGridPlugin, interactionPlugin]}
        initialView="timeGridWeek"
        headerToolbar={{
          left: "prev,next today",
          center: "title",
          right: "timeGridDay,timeGridWeek,dayGridMonth",
        }}
        height="auto"
        slotMinTime="08:00:00"
        slotMaxTime="21:00:00"
        allDaySlot={false}
        nowIndicator
        selectable={false}
        editable={editable}
        eventDurationEditable={false}
        events={events}
        datesSet={handleDatesSet}
        dateClick={onDateClick}
        eventClick={handleEventClick}
        eventDrop={handleEventDrop}
      />
    </div>
  );
}
