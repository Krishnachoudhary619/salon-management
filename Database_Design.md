# Salon Management System — PostgreSQL Database Design

Version: 1.0  
Source of truth: `Salon_Backend_Blueprint.md`, `Salon_Backend_Architecture.md`  
Scope: complete logical schema for V1, plus reserved structures for multi-branch, inventory, and memberships.

This document is design-only. It does not define application code, ORM models, or migrations.

---

## 1. Design principles

1. Every table uses a UUID primary key. Auto-increment integers are forbidden.
2. Every table includes audit fields: `created_at`, `updated_at`, `created_by`, `updated_by`.
3. Every business table supports soft delete: `is_deleted`, `deleted_at`. Hard delete is forbidden.
4. Table names are `snake_case` plural (`users`, `customers`, `appointments`). The staff table is `staff` (mass noun, matches the blueprint).
5. Money is `NUMERIC`, never floating point.
6. Timestamps are `TIMESTAMPTZ` and stored in UTC.
7. Appointment calendar fields stay as `DATE` + `TIME` so availability and calendar queries match the blueprint. Multi-branch will interpret those local values with `branches.timezone`.
8. Historical financial values are snapshotted and never recalculated (`price_snapshot`, `commission_percentage`, `commission_amount`).
9. V1 is a single implicit salon. `branch_id` is present and nullable on the tables named by the architecture so multi-branch can land without a rewrite.
10. Dashboard and performance metrics are **not** stored tables. They are SQL aggregations over appointments, invoices, payments, commissions, and tips.

---

## 2. Shared column conventions

These columns appear on every table unless a table section says otherwise.

### 2.1 Primary key

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | generate UUID v4 | Primary key |

### 2.2 Audit fields

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | Set once on insert |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | Updated on every change |
| `created_by` | `UUID` | YES | `NULL` | Acting user; `NULL` for system/seed |
| `updated_by` | `UUID` | YES | `NULL` | Acting user; `NULL` for system/seed |

Logical reference: `created_by` and `updated_by` point at `users.id`.  
On user delete (soft), leave these values in place. Do not cascade.

### 2.3 Soft delete fields

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `is_deleted` | `BOOLEAN` | NO | `false` | Active rows are `false` |
| `deleted_at` | `TIMESTAMPTZ` | YES | `NULL` | Set only when `is_deleted = true` |

Rules:

- Application queries default to `is_deleted = false`.
- Unique constraints that must survive reuse (email, phone, invoice number) are **partial** uniques on active rows only.
- Soft-deleted rows remain for history and foreign-key integrity.

### 2.4 Multi-branch column (V1-ready, unused until later)

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `branch_id` | `UUID` | YES | `NULL` | Reserved. No foreign key in V1 |

Architecture requires this field now on `staff`, `customers`, `appointments`, and `payments`.  
This design also places it on related operational tables so later modules do not need new columns.

### 2.5 Money and percentages

| Kind | Type | Rules |
|---|---|---|
| Money | `NUMERIC(12,2)` | Scale 2. Must be `>= 0` unless a table allows otherwise |
| Service / line price | `NUMERIC(12,2)` | Must be `> 0` |
| Percentage | `NUMERIC(5,2)` | `0` to `100` inclusive |

### 2.6 Allowed values (application enums)

PostgreSQL should store these as `VARCHAR` with a check constraint (or an equivalent application-enforced enum). Do not use serial lookup tables for these closed sets.

| Domain | Values |
|---|---|
| Role name | `ADMIN`, `RECEPTIONIST`, `STAFF` |
| Staff status | `ACTIVE`, `INACTIVE`, `ON_LEAVE` |
| Appointment status | `PENDING`, `CONFIRMED`, `ARRIVED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`, `NO_SHOW` |
| Payment method | `CASH`, `CARD`, `UPI` |
| Payment status | `PENDING`, `SUCCESS`, `FAILED`, `REFUNDED` |
| Task status | `PENDING`, `IN_PROGRESS`, `COMPLETED` |
| Day of week | `0`–`6` where `0 = Monday` and `6 = Sunday` |
| Future membership status | `ACTIVE`, `EXPIRED`, `CANCELLED` |
| Future stock movement type | `IN`, `OUT`, `ADJUSTMENT` |

---

## 3. Entity relationship overview

```text
roles ─────────┐
               ├── user_roles
users ─────────┤
   │           └── refresh_tokens
   │
   └── staff ── staff_schedules
         │
         ├── appointments ── appointment_services ── services
         │        │
         │        ├── invoices
         │        ├── payments
         │        ├── commissions
         │        └── tips
         │
         └── tasks

customers ──── appointments

Future:
  branches ──────── staff / customers / appointments / payments / …
  customers ─────── customer_memberships ── membership_plans
  appointments ──── appointment_consumed_products ── products
  products ──────── product_stock
```

V1 cardinality:

- One user has many roles.
- One user has at most one staff profile.
- One staff member has many weekly schedule rows.
- One customer has many appointments.
- One appointment has one staff member and one customer.
- One appointment has many services.
- One appointment has at most one invoice.
- One appointment may have many payments (split tender / audit trail).
- One appointment has at most one commission row in V1.
- One appointment may have many tips.
- One staff member has many tasks.

---

## 4. V1 tables

Tables are listed in dependency order.

---

### 4.1 `roles`

**Purpose.** Closed set of application roles used by RBAC. Seeded, not user-managed in V1.

#### Columns

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | UUID v4 | PK |
| `name` | `VARCHAR(32)` | NO | — | `ADMIN`, `RECEPTIONIST`, `STAFF` |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `created_by` | `UUID` | YES | `NULL` | |
| `updated_by` | `UUID` | YES | `NULL` | |
| `is_deleted` | `BOOLEAN` | NO | `false` | |
| `deleted_at` | `TIMESTAMPTZ` | YES | `NULL` | |

#### Constraints

- Primary key: `id`
- Unique (partial): `name` where `is_deleted = false`
- Check: `name` in (`ADMIN`, `RECEPTIONIST`, `STAFF`)

#### Foreign keys

None.

#### Indexes

- Unique index on `name` where `is_deleted = false`
- Index on `is_deleted`

#### Business rules

- Exactly these three roles exist in V1.
- Roles are not deleted in normal operation. Soft delete is reserved for emergency disable.
- Permissions are not stored in the database. They are defined in the application permission matrix.

---

### 4.2 `users`

**Purpose.** Login identities for ADMIN, RECEPTIONIST, and STAFF. Customers are **not** users in V1.

#### Columns

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | UUID v4 | PK |
| `name` | `VARCHAR(120)` | NO | — | Display name |
| `email` | `VARCHAR(255)` | NO | — | Login identifier |
| `password_hash` | `VARCHAR(255)` | NO | — | bcrypt hash only |
| `is_active` | `BOOLEAN` | NO | `true` | Disable without deleting |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `created_by` | `UUID` | YES | `NULL` | Self-referential |
| `updated_by` | `UUID` | YES | `NULL` | |
| `is_deleted` | `BOOLEAN` | NO | `false` | |
| `deleted_at` | `TIMESTAMPTZ` | YES | `NULL` | |

#### Constraints

- Primary key: `id`
- Unique (partial): `lower(email)` where `is_deleted = false`

#### Foreign keys

- `created_by` → `users.id` (optional, `ON DELETE SET NULL`)
- `updated_by` → `users.id` (optional, `ON DELETE SET NULL`)

#### Indexes

- Unique index on `lower(email)` where `is_deleted = false`
- Index on `is_active`
- Index on `is_deleted`

#### Business rules

- Email is the unique login key.
- Passwords are stored only as hashes. Never log `password_hash`.
- `is_active = false` blocks login even if the row is not soft-deleted.
- Soft-deleting a user does not hard-delete staff, appointments, or audit references.
- A user may hold one or more roles via `user_roles`.

---

### 4.3 `user_roles`

**Purpose.** Many-to-many assignment of roles to users.

#### Columns

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | UUID v4 | PK |
| `user_id` | `UUID` | NO | — | |
| `role_id` | `UUID` | NO | — | |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `created_by` | `UUID` | YES | `NULL` | |
| `updated_by` | `UUID` | YES | `NULL` | |
| `is_deleted` | `BOOLEAN` | NO | `false` | |
| `deleted_at` | `TIMESTAMPTZ` | YES | `NULL` | |

#### Constraints

- Primary key: `id`
- Unique (partial): `(user_id, role_id)` where `is_deleted = false`

#### Foreign keys

- `user_id` → `users.id` (`ON DELETE RESTRICT`)
- `role_id` → `roles.id` (`ON DELETE RESTRICT`)

#### Indexes

- Unique index on `(user_id, role_id)` where `is_deleted = false`
- Index on `role_id`
- Index on `is_deleted`

#### Business rules

- A user can have multiple roles (for example STAFF + RECEPTIONIST). Effective permissions are the union.
- Removing a role is a soft delete of this row, not a hard delete.
- JWT access tokens may cache role names; the database remains the source of truth on the next login/refresh.

---

### 4.4 `refresh_tokens`

**Purpose.** Persist refresh tokens so `POST /auth/refresh-token` can rotate them and `POST /auth/logout` can revoke them. Access tokens stay stateless.

#### Columns

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | UUID v4 | PK |
| `user_id` | `UUID` | NO | — | Owner |
| `jti` | `UUID` | NO | — | JWT ID from the token |
| `token_hash` | `VARCHAR(255)` | NO | — | Hash of the refresh token |
| `expires_at` | `TIMESTAMPTZ` | NO | — | |
| `revoked_at` | `TIMESTAMPTZ` | YES | `NULL` | Set on logout or rotation |
| `replaced_by_id` | `UUID` | YES | `NULL` | Next token after rotation |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `created_by` | `UUID` | YES | `NULL` | |
| `updated_by` | `UUID` | YES | `NULL` | |
| `is_deleted` | `BOOLEAN` | NO | `false` | |
| `deleted_at` | `TIMESTAMPTZ` | YES | `NULL` | |

#### Constraints

- Primary key: `id`
- Unique: `jti`
- Unique: `token_hash`

#### Foreign keys

- `user_id` → `users.id` (`ON DELETE RESTRICT`)
- `replaced_by_id` → `refresh_tokens.id` (`ON DELETE SET NULL`)

#### Indexes

- Unique index on `jti`
- Unique index on `token_hash`
- Index on `(user_id, revoked_at, expires_at)`
- Index on `expires_at`

#### Business rules

- Store a hash, never the raw refresh token.
- Logout sets `revoked_at`.
- Refresh rotates: revoke the old row, insert a new row, set `replaced_by_id`.
- Reject expired, revoked, or reused tokens.
- Do not log token values.

---

### 4.5 `staff`

**Purpose.** Salon employees. Linked to a user account. Holds commission configuration used when generating commissions.

#### Columns

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | UUID v4 | PK |
| `user_id` | `UUID` | NO | — | Login account |
| `branch_id` | `UUID` | YES | `NULL` | Future multi-branch |
| `name` | `VARCHAR(120)` | NO | — | May mirror `users.name` |
| `phone` | `VARCHAR(15)` | NO | — | 10–15 digits |
| `designation` | `VARCHAR(80)` | NO | — | Example: Stylist, Colorist |
| `commission_percentage` | `NUMERIC(5,2)` | NO | — | Current configured rate |
| `joining_date` | `DATE` | NO | — | |
| `status` | `VARCHAR(20)` | NO | `'ACTIVE'` | `ACTIVE`, `INACTIVE`, `ON_LEAVE` |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `created_by` | `UUID` | YES | `NULL` | |
| `updated_by` | `UUID` | YES | `NULL` | |
| `is_deleted` | `BOOLEAN` | NO | `false` | |
| `deleted_at` | `TIMESTAMPTZ` | YES | `NULL` | |

#### Constraints

- Primary key: `id`
- Unique (partial): `user_id` where `is_deleted = false`
- Unique (partial): `phone` where `is_deleted = false`
- Check: `commission_percentage` between `0` and `100`
- Check: `status` in (`ACTIVE`, `INACTIVE`, `ON_LEAVE`)

#### Foreign keys

- `user_id` → `users.id` (`ON DELETE RESTRICT`)
- `branch_id` — reserved; FK added when `branches` is implemented

#### Indexes

- Unique index on `user_id` where `is_deleted = false`
- Unique index on `phone` where `is_deleted = false`
- Index on `status`
- Index on `branch_id`
- Index on `is_deleted`
- Index on `name`

#### Business rules

- Every staff row must link to a user. That user should have the `STAFF` role (application-enforced).
- ADMIN and RECEPTIONIST do not require a staff row.
- Soft delete is the only delete path.
- Changing `commission_percentage` affects **future** commissions only. Historical `commissions` rows keep their snapshot.
- Availability and booking require `status = ACTIVE` and `is_deleted = false`.
- `branch_id` is unused in V1 (`NULL`).

---

### 4.6 `services`

**Purpose.** Bookable salon catalog (Hair Cut, Beard Trim, Hair Color, Facial, Hair Spa, and others).

#### Columns

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | UUID v4 | PK |
| `branch_id` | `UUID` | YES | `NULL` | Future per-branch catalog |
| `name` | `VARCHAR(120)` | NO | — | |
| `description` | `TEXT` | YES | `NULL` | |
| `category` | `VARCHAR(80)` | NO | — | Example: Hair, Beard, Color, Facial, Spa |
| `duration_minutes` | `INTEGER` | NO | — | Must be `> 0` |
| `price` | `NUMERIC(12,2)` | NO | — | Current catalog price |
| `is_active` | `BOOLEAN` | NO | `true` | Hide from new bookings |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `created_by` | `UUID` | YES | `NULL` | |
| `updated_by` | `UUID` | YES | `NULL` | |
| `is_deleted` | `BOOLEAN` | NO | `false` | |
| `deleted_at` | `TIMESTAMPTZ` | YES | `NULL` | |

#### Constraints

- Primary key: `id`
- Unique (partial): `(lower(name), coalesce(branch_id, '00000000-0000-0000-0000-000000000000'))` where `is_deleted = false`
- Check: `duration_minutes > 0`
- Check: `price > 0`

#### Foreign keys

- `branch_id` — reserved

#### Indexes

- Unique index on active name per branch (see above)
- Index on `(category, is_active)`
- Index on `is_deleted`
- Index on `branch_id`

#### Business rules

- `is_active = false` hides the service from new bookings without soft-deleting history.
- Catalog price/duration changes do **not** rewrite past `appointment_services` snapshots.
- Only active, non-deleted services may be added to a new appointment.
- `branch_id` is `NULL` in V1 (global catalog).

---

### 4.7 `customers`

**Purpose.** CRM identities for guests. Auto-created during booking when the phone is new.

#### Columns

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | UUID v4 | PK |
| `branch_id` | `UUID` | YES | `NULL` | Future home branch |
| `name` | `VARCHAR(120)` | NO | — | |
| `phone` | `VARCHAR(15)` | NO | — | 10–15 digits; lookup key |
| `email` | `VARCHAR(255)` | YES | `NULL` | |
| `notes` | `TEXT` | YES | `NULL` | Front-desk notes |
| `visit_count` | `INTEGER` | NO | `0` | Denormalized counter |
| `total_spent` | `NUMERIC(12,2)` | NO | `0` | Denormalized spend |
| `last_visit` | `TIMESTAMPTZ` | YES | `NULL` | Last completed visit |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `created_by` | `UUID` | YES | `NULL` | |
| `updated_by` | `UUID` | YES | `NULL` | |
| `is_deleted` | `BOOLEAN` | NO | `false` | |
| `deleted_at` | `TIMESTAMPTZ` | YES | `NULL` | |

#### Constraints

- Primary key: `id`
- Unique (partial): `phone` where `is_deleted = false`
- Unique (partial): `lower(email)` where `email IS NOT NULL` and `is_deleted = false`
- Check: `visit_count >= 0`
- Check: `total_spent >= 0`

#### Foreign keys

- `branch_id` — reserved

#### Indexes

- Unique index on `phone` where `is_deleted = false`
- Unique index on `lower(email)` where email is present and not deleted
- Index on `name`
- Index on `last_visit`
- Index on `branch_id`
- Index on `is_deleted`

#### Business rules

- Phone is the CRM match key. Booking auto-creates a customer when the phone is unknown.
- `visit_count`, `total_spent`, and `last_visit` are maintained by the billing/appointment completion flow. Source of truth for money is `invoices` / `payments`. Source of truth for visits is completed appointments.
- Update those three fields only when an appointment reaches `COMPLETED` and a successful payment exists.
- Customers are not login users in V1.
- Future: a customer may have zero or one active membership (`customer_memberships`).

---

### 4.8 `staff_schedules`

**Purpose.** Weekly working hours used by the availability engine. Prevents booking a staff member who is not working.

#### Columns

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | UUID v4 | PK |
| `staff_id` | `UUID` | NO | — | |
| `branch_id` | `UUID` | YES | `NULL` | Future branch roster |
| `day_of_week` | `SMALLINT` | NO | — | `0` = Monday … `6` = Sunday |
| `start_time` | `TIME` | NO | — | Inclusive |
| `end_time` | `TIME` | NO | — | Exclusive |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `created_by` | `UUID` | YES | `NULL` | |
| `updated_by` | `UUID` | YES | `NULL` | |
| `is_deleted` | `BOOLEAN` | NO | `false` | |
| `deleted_at` | `TIMESTAMPTZ` | YES | `NULL` | |

#### Constraints

- Primary key: `id`
- Check: `day_of_week` between `0` and `6`
- Check: `end_time > start_time` (no overnight shifts in V1)

#### Foreign keys

- `staff_id` → `staff.id` (`ON DELETE RESTRICT`)
- `branch_id` — reserved

#### Indexes

- Index on `(staff_id, day_of_week)` where `is_deleted = false`
- Index on `branch_id`
- Index on `is_deleted`

#### Business rules

- A staff member may have multiple windows on the same day (for example 10:00–13:00 and 15:00–19:00).
- Windows for the same staff + day must not overlap. Enforce in the service layer; an exclusion constraint is optional.
- Booking is allowed only if the appointment interval is fully inside a working window.
- Overnight shifts are out of scope for V1.
- Soft-deleted schedule rows are ignored by the availability engine.

---

### 4.9 `appointments`

**Purpose.** Core booking record. One customer, one staff member, one local date, one time range, many services.

#### Columns

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | UUID v4 | PK |
| `customer_id` | `UUID` | NO | — | |
| `staff_id` | `UUID` | NO | — | Assigned employee |
| `branch_id` | `UUID` | YES | `NULL` | Future multi-branch |
| `appointment_date` | `DATE` | NO | — | Local salon date |
| `start_time` | `TIME` | NO | — | Inclusive |
| `end_time` | `TIME` | NO | — | Exclusive; auto-calculated |
| `status` | `VARCHAR(20)` | NO | `'PENDING'` | See lifecycle |
| `notes` | `TEXT` | YES | `NULL` | |
| `cancelled_at` | `TIMESTAMPTZ` | YES | `NULL` | Set on `CANCELLED` |
| `completed_at` | `TIMESTAMPTZ` | YES | `NULL` | Set on `COMPLETED` |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `created_by` | `UUID` | YES | `NULL` | |
| `updated_by` | `UUID` | YES | `NULL` | |
| `is_deleted` | `BOOLEAN` | NO | `false` | |
| `deleted_at` | `TIMESTAMPTZ` | YES | `NULL` | |

`cancelled_at` and `completed_at` are operational timestamps required by billing, dashboard filters, and status rules. They are not substitutes for `status`.

#### Constraints

- Primary key: `id`
- Check: `end_time > start_time`
- Check: `status` in (`PENDING`, `CONFIRMED`, `ARRIVED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`, `NO_SHOW`)

#### Foreign keys

- `customer_id` → `customers.id` (`ON DELETE RESTRICT`)
- `staff_id` → `staff.id` (`ON DELETE RESTRICT`)
- `branch_id` — reserved

#### Indexes

- Index on `(staff_id, appointment_date, start_time, end_time)` where `is_deleted = false` — overlap checks
- Index on `(appointment_date, status)` — calendar and dashboard
- Index on `customer_id`
- Index on `branch_id`
- Index on `status`
- Index on `completed_at`
- Index on `is_deleted`

#### Business rules

**Lifecycle**

```text
PENDING → CONFIRMED → ARRIVED → IN_PROGRESS → COMPLETED
                 ↘ CANCELLED
                 ↘ NO_SHOW
CONFIRMED → CANCELLED | NO_SHOW
ARRIVED → CANCELLED is not allowed
IN_PROGRESS → CANCELLED is not allowed
COMPLETED is terminal
CANCELLED is terminal
NO_SHOW is terminal
```

- Cannot complete before arriving (`COMPLETED` only from `IN_PROGRESS`, and `IN_PROGRESS` only from `ARRIVED`).
- Cannot arrive after cancellation.
- Cannot reschedule a `COMPLETED`, `CANCELLED`, or `NO_SHOW` appointment.
- An appointment must have at least one `appointment_services` row.
- `end_time = start_time + sum(appointment_services.duration_minutes_snapshot)`.
- Before insert or reschedule, the availability engine must confirm:
  1. Staff exists, is `ACTIVE`, and is not deleted.
  2. Staff has a schedule window covering that weekday and time range.
  3. Duration fits the window.
  4. No overlapping active appointment for that staff (`status` not in `CANCELLED`, `NO_SHOW`; `is_deleted = false`).
- Overlap is a conflict and must be rejected.
- Future: consumed products attach through `appointment_consumed_products`.

---

### 4.10 `appointment_services`

**Purpose.** Line items on an appointment. Supports multiple services and stores immutable price/duration snapshots.

#### Columns

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | UUID v4 | PK |
| `appointment_id` | `UUID` | NO | — | |
| `service_id` | `UUID` | NO | — | Catalog reference |
| `service_name_snapshot` | `VARCHAR(120)` | NO | — | Name at booking time |
| `duration_minutes_snapshot` | `INTEGER` | NO | — | Duration at booking time |
| `price_snapshot` | `NUMERIC(12,2)` | NO | — | Price at booking time |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `created_by` | `UUID` | YES | `NULL` | |
| `updated_by` | `UUID` | YES | `NULL` | |
| `is_deleted` | `BOOLEAN` | NO | `false` | |
| `deleted_at` | `TIMESTAMPTZ` | YES | `NULL` | |

`service_name_snapshot` and `duration_minutes_snapshot` extend the blueprint’s `price_snapshot` so invoices, duration math, and history stay correct after catalog edits.

#### Constraints

- Primary key: `id`
- Check: `duration_minutes_snapshot > 0`
- Check: `price_snapshot > 0`
- Unique (partial): `(appointment_id, service_id)` where `is_deleted = false`  
  Same service may be added twice only if the product later needs quantity; V1 treats one row per service per appointment. If two identical services are required, use two rows and drop this unique constraint in implementation — default V1 rule is **one row per service**.

#### Foreign keys

- `appointment_id` → `appointments.id` (`ON DELETE RESTRICT`)
- `service_id` → `services.id` (`ON DELETE RESTRICT`)

#### Indexes

- Index on `appointment_id`
- Index on `service_id`
- Index on `is_deleted`

#### Business rules

- Snapshots are written at booking (or when the line is added) and never recalculated.
- Invoice `subtotal` = sum of active `price_snapshot` for the appointment.
- Appointment duration = sum of active `duration_minutes_snapshot`.
- Soft-deleting a line requires recalculating `appointments.end_time` if the appointment is still reschedulable.

---

### 4.11 `invoices`

**Purpose.** Financial document generated after an appointment is completed. One invoice per appointment.

#### Columns

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | UUID v4 | PK |
| `appointment_id` | `UUID` | NO | — | |
| `branch_id` | `UUID` | YES | `NULL` | Copied from appointment |
| `invoice_number` | `VARCHAR(40)` | NO | — | Human-readable unique number |
| `subtotal` | `NUMERIC(12,2)` | NO | — | Sum of service snapshots |
| `tax` | `NUMERIC(12,2)` | NO | `0` | Tax amount, not rate |
| `total` | `NUMERIC(12,2)` | NO | — | `subtotal + tax` |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `created_by` | `UUID` | YES | `NULL` | |
| `updated_by` | `UUID` | YES | `NULL` | |
| `is_deleted` | `BOOLEAN` | NO | `false` | |
| `deleted_at` | `TIMESTAMPTZ` | YES | `NULL` | |

#### Constraints

- Primary key: `id`
- Unique (partial): `appointment_id` where `is_deleted = false`
- Unique (partial): `invoice_number` where `is_deleted = false`
- Check: `subtotal >= 0`
- Check: `tax >= 0`
- Check: `total = subtotal + tax`
- Check: `total > 0`

#### Foreign keys

- `appointment_id` → `appointments.id` (`ON DELETE RESTRICT`)
- `branch_id` — reserved

#### Indexes

- Unique index on `appointment_id` where `is_deleted = false`
- Unique index on `invoice_number` where `is_deleted = false`
- Index on `created_at` — revenue-by-day/month aggregations
- Index on `branch_id`
- Index on `is_deleted`

#### Business rules

- Generated only when appointment status becomes `COMPLETED`.
- `subtotal` is the sum of `appointment_services.price_snapshot`.
- Invoice amounts are immutable after creation. Corrections use a new compensating process later (not V1).
- Cannot generate an invoice for `CANCELLED` or `NO_SHOW`.
- Dashboard revenue uses invoices (or successful payments — pick one source; see section 7). This design uses **successful payments** for cash received and **invoices** for ticket size.

---

### 4.12 `payments`

**Purpose.** Payment attempts and successes against an appointment. Provides the payment audit trail.

#### Columns

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | UUID v4 | PK |
| `appointment_id` | `UUID` | NO | — | |
| `branch_id` | `UUID` | YES | `NULL` | Required future field |
| `amount` | `NUMERIC(12,2)` | NO | — | |
| `payment_method` | `VARCHAR(20)` | NO | — | `CASH`, `CARD`, `UPI` |
| `payment_status` | `VARCHAR(20)` | NO | `'PENDING'` | `PENDING`, `SUCCESS`, `FAILED`, `REFUNDED` |
| `paid_at` | `TIMESTAMPTZ` | YES | `NULL` | Required when `SUCCESS` |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `created_by` | `UUID` | YES | `NULL` | |
| `updated_by` | `UUID` | YES | `NULL` | |
| `is_deleted` | `BOOLEAN` | NO | `false` | |
| `deleted_at` | `TIMESTAMPTZ` | YES | `NULL` | |

#### Constraints

- Primary key: `id`
- Check: `amount > 0`
- Check: `payment_method` in (`CASH`, `CARD`, `UPI`)
- Check: `payment_status` in (`PENDING`, `SUCCESS`, `FAILED`, `REFUNDED`)
- Check: if `payment_status = 'SUCCESS'` then `paid_at IS NOT NULL`

#### Foreign keys

- `appointment_id` → `appointments.id` (`ON DELETE RESTRICT`)
- `branch_id` — reserved

#### Indexes

- Index on `appointment_id`
- Index on `(paid_at, payment_status)` — revenue aggregations
- Index on `(payment_status, created_at)`
- Index on `branch_id`
- Index on `is_deleted`

#### Business rules

- A payment belongs to an appointment.
- Cannot record a successful payment on `CANCELLED` or `NO_SHOW`.
- Multiple payment rows are allowed (split CASH + UPI, retries, refunds).
- Appointment is considered paid when `sum(SUCCESS.amount) >= invoices.total`.
- Architecture rule: payment amount (successful total) must be `>=` invoice total. Overpay is allowed; underpay is not a completed payment.
- Successful payment, together with `COMPLETED`, generates `commissions`.
- Do not overwrite a `SUCCESS` row. Refunds are new rows with `REFUNDED` or a dedicated refund amount — V1 records a `REFUNDED` row referencing the same appointment.
- `branch_id` should copy from the appointment when multi-branch is enabled.

---

### 4.13 `commissions`

**Purpose.** Permanent staff earnings from service revenue. Generated once; never recalculated.

#### Columns

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | UUID v4 | PK |
| `appointment_id` | `UUID` | NO | — | |
| `staff_id` | `UUID` | NO | — | Earner |
| `branch_id` | `UUID` | YES | `NULL` | Copied from appointment |
| `service_revenue` | `NUMERIC(12,2)` | NO | — | Base used in the formula |
| `commission_percentage` | `NUMERIC(5,2)` | NO | — | Snapshot from staff at generation |
| `commission_amount` | `NUMERIC(12,2)` | NO | — | Stored result |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `created_by` | `UUID` | YES | `NULL` | System actor allowed |
| `updated_by` | `UUID` | YES | `NULL` | |
| `is_deleted` | `BOOLEAN` | NO | `false` | |
| `deleted_at` | `TIMESTAMPTZ` | YES | `NULL` | |

`service_revenue` is the explicit base so the stored formula is auditable.

#### Constraints

- Primary key: `id`
- Unique (partial): `appointment_id` where `is_deleted = false` (V1: one staff per appointment)
- Check: `service_revenue > 0`
- Check: `commission_percentage` between `0` and `100`
- Check: `commission_amount >= 0`

#### Foreign keys

- `appointment_id` → `appointments.id` (`ON DELETE RESTRICT`)
- `staff_id` → `staff.id` (`ON DELETE RESTRICT`)
- `branch_id` — reserved

#### Indexes

- Unique index on `appointment_id` where `is_deleted = false`
- Index on `staff_id`
- Index on `(staff_id, created_at)`
- Index on `branch_id`
- Index on `is_deleted`

#### Business rules

- Generate only when `appointments.status = COMPLETED` **and** a `payments` row exists with `payment_status = SUCCESS` that completes the invoice.
- Formula: `commission_amount = round(service_revenue * commission_percentage / 100, 2)`.
- `service_revenue` = sum of `appointment_services.price_snapshot`.
- `commission_percentage` is copied from `staff.commission_percentage` at generation time.
- Never recalculate historical commissions if the staff rate later changes.
- Tips are not included in `service_revenue`.
- Receptionists cannot configure `staff.commission_percentage`.

---

### 4.14 `tips`

**Purpose.** Discretionary tips, stored separately from commission and included in performance reports.

#### Columns

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | UUID v4 | PK |
| `appointment_id` | `UUID` | NO | — | |
| `staff_id` | `UUID` | NO | — | |
| `branch_id` | `UUID` | YES | `NULL` | Copied from appointment |
| `amount` | `NUMERIC(12,2)` | NO | — | |
| `notes` | `TEXT` | YES | `NULL` | |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `created_by` | `UUID` | YES | `NULL` | |
| `updated_by` | `UUID` | YES | `NULL` | |
| `is_deleted` | `BOOLEAN` | NO | `false` | |
| `deleted_at` | `TIMESTAMPTZ` | YES | `NULL` | |

#### Constraints

- Primary key: `id`
- Check: `amount > 0`

#### Foreign keys

- `appointment_id` → `appointments.id` (`ON DELETE RESTRICT`)
- `staff_id` → `staff.id` (`ON DELETE RESTRICT`)
- `branch_id` — reserved

#### Indexes

- Index on `appointment_id`
- Index on `staff_id`
- Index on `(staff_id, created_at)`
- Index on `branch_id`
- Index on `is_deleted`

#### Business rules

- Tips are independent of commission.
- Example: revenue `1000`, commission `200`, tip `100` → earnings `300`.
- Multiple tip rows per appointment are allowed (adjustments).
- Soft delete is the correction path in V1.
- Included in team performance (`tips` earned) and excluded from service revenue / commission base.
- Do not create tips for `CANCELLED` appointments.

---

### 4.15 `tasks`

**Purpose.** Work items assigned to staff (non-appointment chores).

#### Columns

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | UUID v4 | PK |
| `assigned_staff_id` | `UUID` | NO | — | |
| `branch_id` | `UUID` | YES | `NULL` | Future branch tasks |
| `title` | `VARCHAR(200)` | NO | — | |
| `description` | `TEXT` | YES | `NULL` | |
| `status` | `VARCHAR(20)` | NO | `'PENDING'` | `PENDING`, `IN_PROGRESS`, `COMPLETED` |
| `due_date` | `DATE` | YES | `NULL` | Optional deadline |
| `completed_at` | `TIMESTAMPTZ` | YES | `NULL` | Set on `COMPLETED` |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `created_by` | `UUID` | YES | `NULL` | Assigner |
| `updated_by` | `UUID` | YES | `NULL` | |
| `is_deleted` | `BOOLEAN` | NO | `false` | |
| `deleted_at` | `TIMESTAMPTZ` | YES | `NULL` | |

#### Constraints

- Primary key: `id`
- Check: `status` in (`PENDING`, `IN_PROGRESS`, `COMPLETED`)
- Check: if `status = 'COMPLETED'` then `completed_at IS NOT NULL`

#### Foreign keys

- `assigned_staff_id` → `staff.id` (`ON DELETE RESTRICT`)
- `branch_id` — reserved

#### Indexes

- Index on `(assigned_staff_id, status)`
- Index on `due_date`
- Index on `branch_id`
- Index on `is_deleted`

#### Business rules

- Staff may view and update their own tasks.
- ADMIN may assign and view all tasks.
- Status moves `PENDING → IN_PROGRESS → COMPLETED`. Completed tasks are not reopened in V1.
- Soft delete hides a task; it is not hard-deleted.

---

## 5. Future tables (designed now, not V1)

These tables are specified so V1 columns and relations do not have to be redesigned. They are **not** part of the V1 migration set.

---

### 5.1 `branches` — multi-branch

**Purpose.** Physical salon locations. V1 operates as a single implicit salon with `branch_id = NULL`.

#### Columns

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | UUID v4 | PK |
| `name` | `VARCHAR(120)` | NO | — | |
| `code` | `VARCHAR(20)` | NO | — | Short unique code |
| `address` | `TEXT` | YES | `NULL` | |
| `phone` | `VARCHAR(15)` | YES | `NULL` | |
| `timezone` | `VARCHAR(64)` | NO | `'Asia/Kolkata'` | IANA zone for local DATE/TIME |
| `is_active` | `BOOLEAN` | NO | `true` | |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `created_by` | `UUID` | YES | `NULL` | |
| `updated_by` | `UUID` | YES | `NULL` | |
| `is_deleted` | `BOOLEAN` | NO | `false` | |
| `deleted_at` | `TIMESTAMPTZ` | YES | `NULL` | |

#### Constraints and indexes

- Unique (partial): `code` where `is_deleted = false`
- Unique (partial): `lower(name)` where `is_deleted = false`
- Index on `is_active`, `is_deleted`

#### When this module ships

Add real foreign keys:

- `staff.branch_id` → `branches.id`
- `customers.branch_id` → `branches.id`
- `appointments.branch_id` → `branches.id`
- `payments.branch_id` → `branches.id`

Also attach FKs for `services`, `staff_schedules`, `invoices`, `commissions`, `tips`, `tasks`, `products`, `product_stock`.

V1 rows stay valid: backfill a default branch or keep `NULL` as “unscoped legacy”.

---

### 5.2 Inventory

Architecture relation: `appointment → consumed products`.

#### 5.2.1 `products`

**Purpose.** Retail or back-bar items that can be sold or consumed.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | UUID v4 | PK |
| `branch_id` | `UUID` | YES | `NULL` | Optional catalog scope |
| `name` | `VARCHAR(160)` | NO | — | |
| `sku` | `VARCHAR(64)` | NO | — | |
| `unit` | `VARCHAR(20)` | NO | `'unit'` | `unit`, `ml`, `g` |
| `is_active` | `BOOLEAN` | NO | `true` | |
| Audit + soft delete | | | | Same shared fields |

Constraints:

- Unique (partial): `sku` where `is_deleted = false`
- Unique (partial): `(lower(name), coalesce(branch_id, zero-uuid))` where `is_deleted = false`

Foreign keys (when implemented): `branch_id` → `branches.id`.

#### 5.2.2 `product_stock`

**Purpose.** Quantity on hand per branch.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | UUID v4 | PK |
| `product_id` | `UUID` | NO | — | |
| `branch_id` | `UUID` | NO | — | Required once multi-branch exists |
| `quantity_on_hand` | `NUMERIC(12,3)` | NO | `0` | |
| Audit + soft delete | | | | Shared fields |

Constraints:

- Unique (partial): `(product_id, branch_id)` where `is_deleted = false`
- Check: `quantity_on_hand >= 0` unless oversell is later allowed

Foreign keys: `product_id` → `products.id`, `branch_id` → `branches.id`.

#### 5.2.3 `appointment_consumed_products`

**Purpose.** Products used during an appointment. This is the reserved inventory join.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | UUID v4 | PK |
| `appointment_id` | `UUID` | NO | — | |
| `product_id` | `UUID` | NO | — | |
| `quantity` | `NUMERIC(12,3)` | NO | — | Must be `> 0` |
| `unit_cost_snapshot` | `NUMERIC(12,2)` | YES | `NULL` | Cost at consumption time |
| Audit + soft delete | | | | Shared fields |

Foreign keys:

- `appointment_id` → `appointments.id`
- `product_id` → `products.id`

Indexes: `(appointment_id)`, `(product_id)`.

Business rules (future):

- Written when the appointment is in progress or completed.
- Decrements `product_stock` for the appointment’s branch.
- Snapshots cost; do not rewrite history after price changes.

---

### 5.3 Memberships

Architecture relation: `customer → membership`.

#### 5.3.1 `membership_plans`

**Purpose.** Sellable plans (monthly, quarterly, annual).

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | UUID v4 | PK |
| `name` | `VARCHAR(120)` | NO | — | |
| `description` | `TEXT` | YES | `NULL` | |
| `price` | `NUMERIC(12,2)` | NO | — | Must be `> 0` |
| `duration_days` | `INTEGER` | NO | — | Must be `> 0` |
| `discount_percentage` | `NUMERIC(5,2)` | NO | `0` | Applied at billing time later |
| `is_active` | `BOOLEAN` | NO | `true` | |
| Audit + soft delete | | | | Shared fields |

Constraints:

- Unique (partial): `lower(name)` where `is_deleted = false`
- Check: `discount_percentage` between `0` and `100`

#### 5.3.2 `customer_memberships`

**Purpose.** A customer’s purchased plan instance.

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NO | UUID v4 | PK |
| `customer_id` | `UUID` | NO | — | |
| `membership_plan_id` | `UUID` | NO | — | |
| `branch_id` | `UUID` | YES | `NULL` | Selling branch |
| `status` | `VARCHAR(20)` | NO | `'ACTIVE'` | `ACTIVE`, `EXPIRED`, `CANCELLED` |
| `started_at` | `DATE` | NO | — | |
| `expires_at` | `DATE` | NO | — | |
| Audit + soft delete | | | | Shared fields |

Constraints:

- Check: `expires_at >= started_at`
- Partial unique: one `ACTIVE` membership per customer (`customer_id` where `status = 'ACTIVE'` and `is_deleted = false`)

Foreign keys:

- `customer_id` → `customers.id`
- `membership_plan_id` → `membership_plans.id`
- `branch_id` → `branches.id` (when branches exist)

Business rules (future):

- Billing may apply `discount_percentage` when creating invoices.
- Expired rows stay for history; do not rewrite `started_at` / `expires_at`.

---

## 6. Tables intentionally omitted from V1

These are listed in the blueprint as future product modules, not schema for this version:

- Inventory movements / purchase orders / vendors (beyond the reserved product tables)
- Expenses
- Loyalty points ledger
- Payroll runs / salary structures
- Notification outbox (WhatsApp / SMS)
- Customer mobile-app devices / OTP

Dashboard and team performance have **no tables**. They read V1 transactional data.

---

## 7. Cross-table business rules

### 7.1 Availability engine (write path)

Before insert or reschedule of an appointment:

1. Staff row exists, `status = ACTIVE`, `is_deleted = false`.
2. A `staff_schedules` row covers `appointment_date`’s weekday and the full `[start_time, end_time)`.
3. `end_time` equals start plus the sum of line-item duration snapshots.
4. No other active appointment for that `staff_id` overlaps the interval.
5. Reject on any failure (`Conflict`).

Active appointments for overlap: `is_deleted = false` and `status` not in (`CANCELLED`, `NO_SHOW`).

### 7.2 Completion and money

```text
Appointment COMPLETED
    → create invoices row (once)
    → accept payments until sum(SUCCESS) >= invoice.total
    → create commissions row (once)
    → increment customers.visit_count, customers.total_spent, customers.last_visit
```

Commission trigger (architecture):

```text
appointment.status = COMPLETED
AND at least one payment.payment_status = SUCCESS covering the invoice
```

### 7.3 Earnings

```text
staff earnings for a period =
    sum(commissions.commission_amount)
  + sum(tips.amount)
```

Do not add tips into `service_revenue` or invoice subtotal.

### 7.4 Soft delete impact

| Deleted record | Effect |
|---|---|
| User | Login blocked; historical `created_by` remains |
| Staff | Cannot be booked; past appointments remain |
| Service | Hidden from catalog; line snapshots remain |
| Customer | Hidden from CRM lists; appointments remain |
| Appointment | Hidden from calendar; child rows remain |
| Schedule | Ignored by availability |

### 7.5 RBAC data implications

- ADMIN: all rows.
- RECEPTIONIST: customers, appointments, schedules, payments, invoices, tips. No commission configuration (`staff.commission_percentage` writes) and no report aggregates.
- STAFF: rows they own — appointments where `staff_id` matches their staff profile, their commissions, tips, and tasks. No customer list, no staff management.

Ownership join: `staff.user_id = current_user.id`.

---

## 8. Aggregation indexes (dashboard and performance)

Dashboard must use SQL aggregates, not in-memory scans. The following indexes exist to support that.

| Query | Driving index |
|---|---|
| Appointments today | `appointments (appointment_date, status)` |
| Monthly / daily revenue | `payments (paid_at, payment_status)` and/or `invoices (created_at)` |
| Average ticket size | `invoices (created_at)` with `avg(total)` |
| Top staff by revenue | `appointments (staff_id, completed_at, status)` + invoice/payment join |
| Staff commissions | `commissions (staff_id, created_at)` |
| Staff tips | `tips (staff_id, created_at)` |
| Customer growth | `customers (created_at)` where `is_deleted = false` |

Recommended metric sources:

| Metric | Source |
|---|---|
| Today’s / monthly revenue | `sum(payments.amount)` where `payment_status = SUCCESS` |
| Appointments today | count of `appointments` on today’s `appointment_date` excluding deleted |
| Customers served | count of distinct `customer_id` on `COMPLETED` appointments |
| Average ticket size | `avg(invoices.total)` |
| Commission earned | `sum(commissions.commission_amount)` |
| Tips earned | `sum(tips.amount)` |

---

## 9. Referential action summary

| Child | Parent | On delete |
|---|---|---|
| `user_roles.user_id` | `users` | Restrict |
| `user_roles.role_id` | `roles` | Restrict |
| `refresh_tokens.user_id` | `users` | Restrict |
| `staff.user_id` | `users` | Restrict |
| `staff_schedules.staff_id` | `staff` | Restrict |
| `appointments.customer_id` | `customers` | Restrict |
| `appointments.staff_id` | `staff` | Restrict |
| `appointment_services.appointment_id` | `appointments` | Restrict |
| `appointment_services.service_id` | `services` | Restrict |
| `invoices.appointment_id` | `appointments` | Restrict |
| `payments.appointment_id` | `appointments` | Restrict |
| `commissions.appointment_id` | `appointments` | Restrict |
| `commissions.staff_id` | `staff` | Restrict |
| `tips.appointment_id` | `appointments` | Restrict |
| `tips.staff_id` | `staff` | Restrict |
| `tasks.assigned_staff_id` | `staff` | Restrict |

No `ON DELETE CASCADE` for business data. Soft delete is the removal mechanism.

`created_by` / `updated_by` may use `ON DELETE SET NULL` if a physical FK is added. They may also remain logical references without a constraint to simplify user bootstrap.

---

## 10. V1 table checklist

| Table | Module | `branch_id` in V1 |
|---|---|---|
| `roles` | Auth | No |
| `users` | Auth | No |
| `user_roles` | Auth | No |
| `refresh_tokens` | Auth | No |
| `staff` | Staff | Yes, nullable |
| `services` | Services | Yes, nullable (extra, safe) |
| `customers` | Customers | Yes, nullable |
| `staff_schedules` | Schedules | Yes, nullable (extra, safe) |
| `appointments` | Appointments | Yes, nullable |
| `appointment_services` | Appointments | No (inherits via appointment) |
| `invoices` | Billing | Yes, nullable (copied) |
| `payments` | Billing | Yes, nullable |
| `commissions` | Commissions | Yes, nullable (copied) |
| `tips` | Tips | Yes, nullable (copied) |
| `tasks` | Tasks | Yes, nullable (extra, safe) |

Architecture-mandated `branch_id` columns: `staff`, `customers`, `appointments`, `payments`.  
The extra nullable columns avoid a second migration when branch-scoped catalog, schedules, invoices, and tasks are needed.

---

## 11. Seed data (logical)

V1 must seed:

| Table | Rows |
|---|---|
| `roles` | `ADMIN`, `RECEPTIONIST`, `STAFF` |
| `users` | At least one active admin |
| `user_roles` | Admin user → `ADMIN` |

Catalog services, staff, and customers are operational data, not schema seeds.

---

## 12. Open implementation notes (non-blocking)

1. **Invoice number format** is an application concern (example: `INV-20260824-0001`). The database only requires uniqueness among active rows.
2. **Tax rate** is not stored in V1; `invoices.tax` is an amount. A rate snapshot can be added later without breaking `total = subtotal + tax`.
3. **`user_roles` vs JWT claims**: roles in the token are a cache. Refresh should reload from `user_roles`.
4. **Partial unique indexes** are required so a soft-deleted email/phone/invoice number can be reused.
5. Future `branches`, inventory, and membership tables must not change V1 primary keys or snapshot columns.
