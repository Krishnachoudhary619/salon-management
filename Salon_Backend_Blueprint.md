# Salon Management System - Backend Development Blueprint

## Project Overview

Build a modular FastAPI backend for a Salon Management System.

### Tech Stack
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0
- Alembic
- Pydantic
- JWT Authentication
- RBAC (Role Based Access Control)

---

# Module 1: Authentication & Authorization

## Objective
Provide secure authentication and role-based authorization.

### Roles
- ADMIN
- RECEPTIONIST
- STAFF

### Tables
#### users
- id
- name
- email
- password_hash
- is_active
- created_at

#### roles
- id
- name

#### user_roles
- user_id
- role_id

### APIs
- POST /auth/login
- POST /auth/logout
- GET /auth/me
- POST /auth/refresh-token

### Deliverables
- JWT Authentication
- Password Hashing
- RBAC Middleware
- Protected Routes

---

# Module 2: Staff Management

## Objective
Manage salon employees.

### Table: staff
- id
- user_id
- name
- phone
- designation
- commission_percentage
- joining_date
- status

### APIs
- GET /staff
- GET /staff/{id}
- POST /staff
- PUT /staff/{id}
- DELETE /staff/{id}

### Business Rules
- Staff linked to user account
- Commission percentage configurable
- Soft delete preferred

---

# Module 3: Service Management

## Objective
Manage salon services.

### Table: services
- id
- name
- description
- category
- duration_minutes
- price
- is_active

### APIs
- GET /services
- POST /services
- PUT /services/{id}
- DELETE /services/{id}

### Example Services
- Hair Cut
- Beard Trim
- Hair Color
- Facial
- Hair Spa

---

# Module 4: Customer Management

## Objective
Maintain customer CRM.

### Table: customers
- id
- name
- phone
- email
- notes
- visit_count
- total_spent
- last_visit

### APIs
- GET /customers
- GET /customers/{id}
- POST /customers
- PUT /customers/{id}

### Business Rules
- Auto-create customer during booking
- Track spending and visits

---

# Module 5: Staff Availability

## Objective
Prevent double booking.

### Table: staff_schedules
- id
- staff_id
- day_of_week
- start_time
- end_time

### APIs
- GET /staff-schedules
- POST /staff-schedules
- PUT /staff-schedules/{id}

### Validation Rules
- Staff must be working
- No overlapping appointments
- Slot must fit service duration

---

# Module 6: Appointment Management

## Objective
Core booking system.

### Table: appointments
- id
- customer_id
- staff_id
- appointment_date
- start_time
- end_time
- status
- notes

### Table: appointment_services
- id
- appointment_id
- service_id
- price_snapshot

### Status Flow
- PENDING
- CONFIRMED
- ARRIVED
- IN_PROGRESS
- COMPLETED
- CANCELLED
- NO_SHOW

### APIs
- POST /appointments
- GET /appointments
- GET /appointments/calendar
- GET /appointments/{id}
- PATCH /appointments/{id}/status
- PATCH /appointments/{id}/reschedule

### Business Rules
- Support multiple services per appointment
- Validate staff availability
- Auto-calculate duration

---

# Module 7: Billing & Payments

## Objective
Track payments and invoices.

### Table: payments
- id
- appointment_id
- amount
- payment_method
- payment_status
- paid_at

### Table: invoices
- id
- appointment_id
- invoice_number
- subtotal
- tax
- total

### Payment Methods
- CASH
- CARD
- UPI

### APIs
- POST /payments
- GET /payments
- GET /invoices/{id}

### Business Rules
- Invoice generated after completion
- Store payment audit trail

---

# Module 8: Commission Management

## Objective
Calculate staff earnings.

### Table: commissions
- id
- appointment_id
- staff_id
- commission_percentage
- commission_amount

### APIs
- GET /commissions
- GET /commissions/staff/{id}

### Business Rules
- Auto-generated after payment completion
- Based on service revenue

---

# Module 9: Tips Management

## Objective
Track staff tips.

### Table: tips
- id
- appointment_id
- staff_id
- amount
- notes

### APIs
- POST /tips
- GET /tips
- GET /tips/staff/{id}

### Business Rules
- Separate from commission
- Included in performance reports

---

# Module 10: Task Management

## Objective
Assign staff tasks.

### Table: tasks
- id
- assigned_staff_id
- title
- description
- status
- due_date

### Status
- PENDING
- IN_PROGRESS
- COMPLETED

### APIs
- POST /tasks
- GET /tasks
- PUT /tasks/{id}

---

# Module 11: Dashboard & Analytics

## Objective
Generate salon metrics.

### Dashboard Cards
- Today's Revenue
- Monthly Revenue
- Appointments Today
- Customers Served
- Average Ticket Size

### APIs
- GET /dashboard/overview
- GET /dashboard/revenue
- GET /dashboard/appointments
- GET /dashboard/top-performers

### KPIs
- Revenue by Day
- Revenue by Month
- Customer Growth
- Staff Performance

---

# Module 12: Team Performance

## Objective
Track staff productivity.

### Metrics
- Customers Served
- Revenue Generated
- Commission Earned
- Tips Earned
- Appointments Completed

### APIs
- GET /performance/team
- GET /performance/staff/{id}

---

# Common Backend Standards

## Folder Structure

```text
app/
├── auth/
├── users/
├── staff/
├── services/
├── customers/
├── appointments/
├── schedules/
├── billing/
├── commissions/
├── tips/
├── tasks/
├── dashboard/
├── core/
├── database/
├── common/
```

## Requirements

Each module should contain:

- models.py
- schemas.py
- repository.py
- service.py
- router.py
- dependencies.py

## API Standards

- Pagination
- Filtering
- Sorting
- Global Exception Handling
- Request Validation
- Swagger Documentation

## Audit Fields

Every table should include:

- created_at
- updated_at
- created_by
- updated_by

---

# Future Modules (Not V1)

- Inventory Management
- Expense Management
- Loyalty Program
- Membership Plans
- Multi Branch Support
- Payroll Management
- WhatsApp Notifications
- SMS Notifications
- Customer Mobile App
