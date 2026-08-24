# Salon Management System
# Backend Architecture & Engineering Standards
# Master Reference for AI Agents

Version: 1.0

---

# 1. Project Goal

Build a scalable Salon Management System backend using:

- FastAPI
- PostgreSQL
- SQLAlchemy 2.0
- Alembic
- Pydantic v2
- JWT Authentication
- RBAC

The architecture should support future modules without major refactoring.

Future expansion:

- Multi Branch
- Inventory
- Memberships
- Payroll
- Mobile App
- WhatsApp Integrations

---

# 2. Architecture Principles

Follow:

### Clean Architecture

```text
Router
  ↓
Service
  ↓
Repository
  ↓
Database
```

Rules:

- Router contains no business logic.
- Service contains business logic.
- Repository contains database queries.
- Models contain database structure.
- Schemas contain request/response contracts.

---

# 3. Folder Structure

```text
app/

├── main.py

├── core/
│   ├── config.py
│   ├── security.py
│   ├── exceptions.py
│   ├── permissions.py
│   └── constants.py

├── database/
│   ├── base.py
│   ├── session.py
│   └── migrations/

├── common/
│   ├── responses.py
│   ├── pagination.py
│   └── enums.py

├── auth/
├── users/
├── staff/
├── services/
├── customers/
├── schedules/
├── appointments/
├── billing/
├── commissions/
├── tips/
├── tasks/
├── dashboard/

tests/
```

---

# 4. Module Structure

Every module MUST contain:

```text
staff/

├── models.py
├── schemas.py
├── repository.py
├── service.py
├── router.py
├── dependencies.py
```

---

# 5. Database Standards

## Primary Keys

Use UUID.

Example:

```python
id = Column(UUID(as_uuid=True), primary_key=True)
```

Never use auto increment IDs.

---

## Audit Fields

Every table MUST include:

```python
created_at
updated_at
created_by
updated_by
```

Example:

```python
created_at = Column(DateTime(timezone=True))
updated_at = Column(DateTime(timezone=True))

created_by = Column(UUID)
updated_by = Column(UUID)
```

---

## Soft Delete

Never hard delete business records.

Use:

```python
is_deleted = Column(Boolean, default=False)
deleted_at = Column(DateTime)
```

---

# 6. Naming Conventions

## Tables

snake_case plural

Examples:

```text
users
staff
customers
appointments
```

---

## API Routes

```text
/api/v1/staff
/api/v1/customers
/api/v1/appointments
```

---

## Service Classes

```python
StaffService
CustomerService
AppointmentService
```

---

## Repository Classes

```python
StaffRepository
CustomerRepository
AppointmentRepository
```

---

# 7. Authentication

## JWT

Access Token

Refresh Token

---

## Login Response

```json
{
  "access_token": "",
  "refresh_token": "",
  "user": {}
}
```

---

## Protected Routes

Use dependency injection.

Example:

```python
Depends(get_current_user)
```

---

# 8. Authorization (RBAC)

Roles:

```text
ADMIN
RECEPTIONIST
STAFF
```

---

## Permissions Matrix

### ADMIN

Can access:

- everything

### RECEPTIONIST

Can access:

- customers
- appointments
- schedules

Cannot access:

- reports
- commission configuration

### STAFF

Can access:

- own appointments
- own earnings
- own tasks

Cannot access:

- customers list
- reports
- staff management

---

# 9. API Response Standard

All APIs MUST follow:

Success:

```json
{
  "success": true,
  "message": "Operation successful",
  "data": {}
}
```

---

Error:

```json
{
  "success": false,
  "message": "Validation error",
  "errors": []
}
```

---

# 10. Pagination Standard

Every list endpoint:

```http
GET /customers
```

Must support:

```text
page
limit
search
sort_by
sort_order
```

Response:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "limit": 20
}
```

---

# 11. Validation Rules

Validate at schema level.

Examples:

Phone:

```python
10-15 digits
```

Email:

```python
EmailStr
```

Price:

```python
Must be > 0
```

Duration:

```python
Must be > 0
```

---

# 12. Logging Standards

Use structured logging.

Log:

- login
- appointment creation
- payment creation
- status changes

Do NOT log:

- passwords
- tokens

---

# 13. Exception Handling

Create centralized exception handlers.

Examples:

```python
NotFoundException

ValidationException

PermissionDeniedException

ConflictException
```

---

# 14. Appointment Business Rules

This is the core module.

Appointment lifecycle:

```text
PENDING
CONFIRMED
ARRIVED
IN_PROGRESS
COMPLETED
CANCELLED
NO_SHOW
```

Rules:

- Cannot complete before arriving.
- Cannot arrive after cancellation.
- Cannot reschedule completed appointment.
- Must validate availability before booking.

---

# 15. Availability Engine

Before creating appointment:

Check:

1. Staff exists.
2. Staff working that day.
3. Slot available.
4. Duration fits.
5. No overlap.

Reject if conflict exists.

---

# 16. Payment Rules

Payment belongs to appointment.

Appointment can have:

```text
CASH
CARD
UPI
```

Rules:

- Payment amount >= invoice total.
- Cannot pay cancelled appointment.
- Payment generates financial records.

---

# 17. Commission Rules

Commission generated when:

```text
Appointment = COMPLETED
AND
Payment = SUCCESS
```

Formula:

```text
Service Revenue × Commission %
```

Store calculated amount permanently.

Never recalculate historical commissions.

---

# 18. Tip Rules

Tips are separate from commission.

Example:

Revenue = 1000

Commission = 200

Tip = 100

Total Earnings = 300

---

# 19. Dashboard Rules

Dashboard must use aggregated queries.

Never load all records and calculate in memory.

Use SQL aggregations.

Metrics:

- Revenue Today
- Revenue Month
- Appointments Today
- Average Ticket Size
- Top Staff

---

# 20. Performance Standards

Avoid N+1 queries.

Use:

```python
joinedload()
selectinload()
```

For relationships.

---

# 21. Testing Standards

Every module must have:

```text
Unit Tests
Integration Tests
```

Coverage target:

```text
80%
```

---

# 22. API Documentation

Swagger available at:

```text
/docs
```

Redoc:

```text
/redoc
```

Every endpoint must include:

- Summary
- Description
- Tags

---

# 23. Environment Variables

```env
APP_NAME=Salon Backend

DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=

JWT_SECRET=

ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
```

---

# 24. Future Ready Design

Prepare architecture for:

### Multi Branch

Future field:

```python
branch_id
```

on:

- staff
- customers
- appointments
- payments

---

### Inventory

Future relation:

```python
appointment
→ consumed products
```

---

### Membership

Future relation:

```python
customer
→ membership
```

---

# 25. Development Order

Phase 1

- Auth
- Staff
- Services
- Customers

Phase 2

- Schedules
- Appointments
- Availability Engine

Phase 3

- Billing
- Payments
- Commissions
- Tips

Phase 4

- Tasks
- Dashboard
- Team Performance

---

# 26. AI Agent Instructions

For every module generate:

1. SQLAlchemy Models
2. Pydantic Schemas
3. Repository Layer
4. Service Layer
5. Router Layer
6. Unit Tests
7. Alembic Migration

Never place business logic in routers.

Always use dependency injection.

Always return standardized API responses.

Always follow RBAC rules.

Always include pagination for list APIs.

Always include audit fields.

This document is the source of truth for backend development.
