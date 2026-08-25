export { apiClient, apiRequest, apiRequestOptional, registerUnauthorizedHandler } from "./client";
export { ApiError, getErrorMessage, getFieldErrors, isApiError, normalizeAxiosError } from "./errors";
export { fetchCurrentUser, login, logout } from "./auth";
export {
  fetchAppointmentSeries,
  fetchDashboardOverview,
  fetchRevenueSeries,
  fetchTopPerformers,
} from "./dashboard";
export { fetchUpcomingAppointments } from "./appointments";
export {
  cancelAppointment,
  createAppointment,
  fetchAppointment,
  fetchAppointmentCalendar,
  fetchAppointments,
  fetchCalendarAppointments,
  rescheduleAppointment,
  updateAppointment,
} from "./appointments";
export {
  createService,
  deactivateService,
  fetchServices,
  updateService,
} from "./services";
export {
  createStaff,
  deactivateStaff,
  fetchStaff,
  fetchStaffMember,
  updateStaff,
} from "./staff";
export { fetchCustomer, fetchCustomers, createCustomer } from "./customers";
export { fetchAvailability } from "./availability";
export { fetchCommission, fetchCommissions, fetchStaffCommissions } from "./commissions";
export { fetchInvoice, fetchInvoiceByAppointment, fetchInvoices } from "./invoices";
export { createPayment, fetchPayments } from "./payments";
export { fetchStaffPerformance, fetchTeamPerformance } from "./performance";
export { createTip, fetchTip, fetchTips, updateTip } from "./tips";
export { createTask, fetchTask, fetchTasks, updateTask } from "./tasks";
