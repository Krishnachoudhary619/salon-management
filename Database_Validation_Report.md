# Database Validation Report

**Role.** Principal Backend Architect  
**Date.** 2026-08-24  
**Action.** Review only. No schema, model, migration, or seeder changes in this pass.

**Sources compared**

| Layer | Location |
|---|---|
| Approved design | `Database_Design.md`, `ERD.md` |
| Prior design review | `Database_Review_Report.md` (P0/P1 not applied; those fixes were not approved) |
| Architecture | `Salon_Backend_Architecture.md`, `Salon_Backend_Blueprint.md` |
| ORM | `backend/app/**/models.py`, `backend/app/database/base.py` |
| Registry | `backend/app/database/models.py` |
| Migration | `0001_foundation` (empty) → `0002_create_v1_schema` |
| Seed | `backend/app/database/seed.py` |

This report validates **implementation against the approved V1 design**, not whether that design should change. Inherited design risks that are still true in code are listed separately so they are not mistaken for implementation bugs.

---

## 1. Verdict

The V1 database implementation **matches the approved design** for tables, foreign keys, check constraints, partial uniques, enum storage, `branch_id` placement, and ORM cardinality.

It is **ready as a schema foundation** for auth, staff, services, and customers.

It is **not yet sufficient to protect booking or money at the database layer**. The approved design left overlap, financial immutability, and several dashboard indexes to the application (or to later work). The models and migration faithfully reproduced that choice. They did not add the P0/P1 schema fixes from `Database_Review_Report.md`.

**Ship the schema for Modules 1–5.** Do not treat appointments or billing as integrity-complete until the inherited P0 items are either accepted as application-only risk or fixed in a later migration.

---

## 2. Inventory

| Item | Expected (design) | Implemented | Status |
|---|---|---|---|
| V1 tables | 15 | 15 mapped + migrated | Pass |
| Future tables | `branches`, `products`, `product_stock`, `appointment_consumed_products`, `membership_plans`, `customer_memberships` | Not created | Pass (reserved, not V1) |
| Dashboard tables | None (aggregates only) | `dashboard/models.py` is a comment only | Pass |
| Enum storage | `VARCHAR` + `CHECK`, not PostgreSQL `ENUM` | Same | Pass |
| UUID PKs | All tables | All tables | Pass |
| Audit + soft delete | Every table | Mixins on every mapped table | Pass |
| `branch_id` | Per design checklist | Matches checklist | Pass |
| Alembic head | Create V1 schema | `0002_create_v1_schema` | Pass |
| Seed | Roles + admin | Roles, admin, plus sample staff/services | Pass with note |

Mapped tables: `roles`, `users`, `user_roles`, `refresh_tokens`, `staff`, `services`, `customers`, `staff_schedules`, `appointments`, `appointment_services`, `invoices`, `payments`, `commissions`, `tips`, `tasks`.

---

## 3. Relationships

Every ERD V1 edge is present as a SQLAlchemy `relationship` with `back_populates`, except the token rotation self-link (one-way by design).

### 3.1 Cardinality (ORM vs ERD)

| Parent → child | ERD | ORM | Notes |
|---|---|---|---|
| `users` → `user_roles` | 1 → N | `User.user_roles` list, `selectin` | Pass |
| `roles` → `user_roles` | 1 → N | `Role.user_roles` list, `selectin` | Pass |
| `users` → `refresh_tokens` | 1 → N | `User.refresh_tokens` list, `selectin` | Pass |
| `refresh_tokens` → `refresh_tokens` | 0..1 → 0..1 | `RefreshToken.replaced_by`, `uselist=False` | Pass; no reverse collection |
| `users` → `staff` | 1 → 0..1 | `User.staff` `uselist=False`; `Staff.user` many-to-one | Pass |
| `staff` → `staff_schedules` | 1 → N | `Staff.schedules` | Pass |
| `staff` → `appointments` | 1 → N | `Staff.appointments` | Pass |
| `customers` → `appointments` | 1 → N | `Customer.appointments` | Pass |
| `appointments` → `appointment_services` | 1 → N | `Appointment.appointment_services` | Pass |
| `services` → `appointment_services` | 1 → N | `Service.appointment_services` | Pass |
| `appointments` → `invoices` | 1 → 0..1 | `Appointment.invoice` `uselist=False` | Pass |
| `appointments` → `payments` | 1 → N | `Appointment.payments` | Pass |
| `appointments` → `commissions` | 1 → 0..1 | `Appointment.commission` `uselist=False` | Pass |
| `staff` → `commissions` | 1 → N | `Staff.commissions` | Pass |
| `appointments` → `tips` | 1 → N | `Appointment.tips` | Pass |
| `staff` → `tips` | 1 → N | `Staff.tips` | Pass |
| `staff` → `tasks` | 1 → N | `Staff.tasks` ↔ `Task.assigned_staff` | Pass |

No delete-orphan or `ON DELETE CASCADE` is configured on relationships (`save-update, merge` only). That matches Restrict + soft delete.

Customers are not users. There is no `Customer` ↔ `User` relationship. Correct.

### 3.2 Relationship issues (implementation)

| ID | Severity | Finding |
|---|---|---|
| R1 | P2 | Many-to-one relations default to `lazy="select"` (`Appointment.customer`, `Staff.user`, `Invoice.appointment`, and similar). Async SQLAlchemy will raise `MissingGreenlet` if those attributes are accessed without an explicit load. Collections correctly use `selectin`. Repositories must `selectinload` / `joinedload` parents, or parent relations should be `lazy="selectin"`. |
| R2 | P2 | `Staff.appointments` (and similar large collections) use `selectin`. Loading a staff row will pull every historical appointment. Fine for V1 volume; later list endpoints should not rely on this default. |
| R3 | P3 | `RefreshToken.replaced_by` has no `back_populates`. Rotation can walk old → new, not new → old. Acceptable. |
| R4 | P3 | `appointment_services` has no `order_by`. Line order is insert order / unordered. Invoice reprints will need an explicit sort (for example `created_at`). |
| R5 | P3 | No ORM relationship for `created_by` / `updated_by` or `branch_id`. Matches the design (logical UUIDs, no `branches` table). |

There are no orphan relationships (relationship without an FK) and no business FKs without an ORM relationship.

---

## 4. Foreign keys

### 4.1 Enforced FKs (models + migration)

All use `ON DELETE RESTRICT` except token replacement.

| Child | Parent | On delete | In models | In `0002` |
|---|---|---|---|---|
| `user_roles.user_id` | `users.id` | Restrict | Yes | Yes |
| `user_roles.role_id` | `roles.id` | Restrict | Yes | Yes |
| `refresh_tokens.user_id` | `users.id` | Restrict | Yes | Yes |
| `refresh_tokens.replaced_by_id` | `refresh_tokens.id` | Set null | Yes | Yes |
| `staff.user_id` | `users.id` | Restrict | Yes | Yes |
| `staff_schedules.staff_id` | `staff.id` | Restrict | Yes | Yes |
| `appointments.customer_id` | `customers.id` | Restrict | Yes | Yes |
| `appointments.staff_id` | `staff.id` | Restrict | Yes | Yes |
| `appointment_services.appointment_id` | `appointments.id` | Restrict | Yes | Yes |
| `appointment_services.service_id` | `services.id` | Restrict | Yes | Yes |
| `invoices.appointment_id` | `appointments.id` | Restrict | Yes | Yes |
| `payments.appointment_id` | `appointments.id` | Restrict | Yes | Yes |
| `commissions.appointment_id` | `appointments.id` | Restrict | Yes | Yes |
| `commissions.staff_id` | `staff.id` | Restrict | Yes | Yes |
| `tips.appointment_id` | `appointments.id` | Restrict | Yes | Yes |
| `tips.staff_id` | `staff.id` | Restrict | Yes | Yes |
| `tasks.assigned_staff_id` | `staff.id` | Restrict | Yes | Yes |

Names follow the metadata convention (`fk_<table>_<column>_<referred>`). Constraint names in the compiled migration SQL match the ORM.

No `ON DELETE CASCADE` on business data. Pass.

### 4.2 Intentionally missing FKs

| Column | Design | Implementation | Assessment |
|---|---|---|---|
| `created_by` / `updated_by` | Optional FK `ON DELETE SET NULL`, or logical UUID | Logical UUID, no FK | Allowed by design §9. Bootstrap and seed stay simple. Orphan actor UUIDs are possible. |
| `branch_id` | Reserved; no FK in V1 | Nullable UUID, indexed, no FK | Matches design. Orphan values can be written until `branches` exists. |
| `payments.invoice_id` | Not in approved V1 | Absent | Matches approved design. Prior review still recommends it before billing production. |

---

## 5. Indexes

### 5.1 Present and aligned with table-level design

Mixin indexes `ix_<table>_is_deleted` and `ix_<table>_branch_id` exist wherever the mixins apply.

Partial unique / query indexes from `Database_Design.md` §4 are implemented, including:

- `uq_roles_name_active`
- `uq_users_email_active` on `lower(email)`
- `uq_user_roles_user_role_active`
- `uq_staff_user_id_active`, `uq_staff_phone_active`
- `uq_services_name_branch_active` on `lower(name), coalesce(branch_id, zero-uuid)`
- `uq_customers_phone_active`, `uq_customers_email_active` (`email IS NOT NULL AND is_deleted = false`)
- `ix_staff_schedules_staff_day_active` (partial, not unique)
- `ix_appointments_staff_slot_active` (B-tree partial; not GiST)
- `uq_appointment_services_appointment_service_active`
- `uq_invoices_appointment_id_active`, `uq_invoices_invoice_number_active`
- `uq_commissions_appointment_id_active`
- Payment, commission, tip, and task query indexes listed on those tables

Full uniques (not partial): `uq_refresh_tokens_jti`, `uq_refresh_tokens_token_hash`. Matches design.

### 5.2 Missing versus design §8 (dashboard)

These indexes were promised for aggregations and are **not** on the table definitions or in `0002`.

| Gap | Design §8 | Severity |
|---|---|---|
| `appointments (staff_id, completed_at, status)` | Top staff by revenue | P2 |
| `customers (created_at)` where active | Customer growth | P2 |

Table-level §4 did not list them either. Implementation followed §4, not §8. Dashboard Module 11 will either sequential-scan or need a follow-up migration.

### 5.3 Index quality (not a spec miss)

| Observation | Impact |
|---|---|
| Single-column `is_deleted` indexes | Low selectivity; the planner often ignores them. Partial indexes `WHERE is_deleted = false` on real filter columns would be stronger. |
| Appointment overlap index is B-tree | Speeds equality/range lookups; does **not** enforce non-overlap. |
| `ix_user_roles_user_id` omitted | Covered as leftmost column of `uq_user_roles_user_role_active`. Fine. |
| UUID v4 PKs | Random inserts fragment B-trees. Acceptable for a single salon. |

---

## 6. Constraints

### 6.1 Check constraints — present

| Table | Constraint | Status |
|---|---|---|
| `roles` | `name IN (ADMIN, RECEPTIONIST, STAFF)` | Pass |
| `staff` | status allowed; commission 0–100 | Pass |
| `services` | `duration_minutes > 0`, `price > 0` | Pass |
| `customers` | `visit_count >= 0`, `total_spent >= 0` | Pass |
| `staff_schedules` | `day_of_week BETWEEN 0 AND 6`, `end_time > start_time` | Pass |
| `appointments` | status allowed; `end_time > start_time` | Pass |
| `appointment_services` | snapshot duration/price `> 0` | Pass |
| `invoices` | subtotal/tax ≥ 0, `total = subtotal + tax`, `total > 0` | Pass |
| `payments` | amount > 0; method/status allowed; SUCCESS requires `paid_at` | Pass |
| `commissions` | revenue > 0; percentage 0–100; amount ≥ 0 | Pass |
| `tips` | amount > 0 | Pass |
| `tasks` | status allowed; COMPLETED requires `completed_at` | Pass |

Naming in the database is `ck_<table>_<name>` via the metadata convention. Migration short names expand correctly (verified against compiled SQL).

Enums are Python `StrEnum` stored as `VARCHAR(20|32)` with CHECKs. Adding a value later is a CHECK-alter migration, not `ALTER TYPE`. That is the right extensibility choice.

### 6.2 Unique constraints — present

Partial uniques on active rows match the reuse-after-soft-delete rule. Invoice number and appointment-scoped invoice/commission 1–0..1 are partial, so a soft-deleted financial row unlocks a second insert. That is specified, not an accident.

### 6.3 Constraints in the design that are application-only

These rules exist in `Database_Design.md` business-rules sections and are **not** in SQL. Implementation is consistent with that (no missing CHECK that the approved table spec required).

| Rule | Risk if only enforced in services |
|---|---|
| Appointment slots do not overlap | Double-booking under concurrency |
| Schedule windows on the same staff/day do not overlap | Double-assigned availability |
| `cancelled_at` / `completed_at` stay in sync with status | Dashboard and billing filters drift |
| `is_deleted` xor `deleted_at` | Half-deleted rows |
| Phone is 10–15 digits | Architecture rule; columns are `VARCHAR(15)` only |
| Invoice only for `COMPLETED` appointments | Invoice on a pending booking |
| SUCCESS payment not allowed on CANCELLED / NO_SHOW | Paid cancelled visits |
| `commissions.staff_id = appointments.staff_id` | Commission paid to the wrong employee |
| `commission_amount = round(service_revenue * percentage / 100, 2)` | Stored math can disagree with formula |
| At least one `appointment_services` row | Empty appointments |

### 6.4 Small type drift vs design

Design types `TEXT` for `services.description`, `customers.notes`, `appointments.notes`, `tasks.description`, `tips.notes`. Models use unbounded `String()` which compiles to PostgreSQL `VARCHAR` with no length. Storage and behavior are equivalent in PostgreSQL. Cosmetic only (P3).

`id` has a Python `default=uuid4` and **no** `server_default` (`gen_random_uuid()`). ORM inserts are fine. Raw SQL inserts without `id` will fail. P3.

`updated_at` has ORM `onupdate` and DB `DEFAULT now()` but **no** update trigger. Bulk SQL updates will leave `updated_at` stale. P3.

---

## 7. Migration fidelity

| Check | Result |
|---|---|
| Revision chain | `0001_foundation` (no-op) → `0002_create_v1_schema` (head) |
| Alembic `target_metadata` | `Base.metadata` after importing `app.database.models` |
| Table create order | Respects FK dependencies |
| Downgrade | Drops children before parents |
| FK / CHECK / index names | Match ORM naming convention |
| Partial `postgresql_where` | Present on the same indexes as the models |
| Native PG enums | Not used |
| `compare_type` / `compare_server_default` | Enabled in `env.py` |

`0002` is handwritten to match models. Compiled `alembic upgrade head --sql` previously matched model DDL.

This review did **not** apply the migration to PostgreSQL. Live `alembic upgrade head` should be run before Module 1.

---

## 8. Future extensibility

### 8.1 What V1 already reserved well

| Capability | How V1 prepared | Later change |
|---|---|---|
| Multi-branch | Nullable indexed `branch_id` on staff, customers, appointments, payments (architecture-required) **and** on services, schedules, invoices, commissions, tips, tasks (design extras) | Add `branches`, then `ALTER … ADD CONSTRAINT` FKs. Do not add `branch_id` columns later. |
| Per-branch catalog | Unique `(lower(name), coalesce(branch_id, zero-uuid))` | `NULL` remains “global catalog”; a real branch UUID becomes a second catalog without rewriting the unique. |
| Inventory | No V1 table; appointment snapshots do not include products | Add `products`, `product_stock`, `appointment_consumed_products` without changing `appointment_services` PK/snapshots. |
| Memberships | `customers` has no membership column | Add `membership_plans` + `customer_memberships`. |
| Catalog price changes | `appointment_services` name/duration/price snapshots | Historical invoices stay correct. |
| Commission rate changes | Stored `service_revenue`, `percentage`, `amount` | Historical pay stays correct. |
| New appointment/payment/task statuses | VARCHAR + CHECK | New migration to widen CHECK + Python enum. Avoid PostgreSQL ENUM. |
| Soft-delete reuse | Partial uniques | Soft-deleted email/phone/invoice number can be reused. |
| Dashboard | No KPI tables | New metrics are queries + indexes, not new fact tables. |

`appointment_services` correctly has **no** `branch_id` (inherits via appointment).

### 8.2 Extensibility risks

| ID | Severity | Risk |
|---|---|---|
| E1 | P2 | `branch_id` has no `CHECK (branch_id IS NULL)` and no FK. A typo UUID in V1 will block `ADD CONSTRAINT` when `branches` ships. |
| E2 | P2 | Payments hang off `appointment_id` only. Multi-invoice or void/reissue later needs `invoice_id` (and likely a backfill). |
| E3 | P2 | Unique `(appointment_id, service_id)` forbids two identical catalog items on one ticket. Adding `quantity` later is a breaking product decision (or dropping the unique). |
| E4 | P3 | UUIDv4 PKs. High-write multi-branch later may want UUIDv7 on **new** tables only; V1 PKs should stay. |
| E5 | P3 | `customers.visit_count` / `total_spent` / `last_visit` are denormalized. Refunds and memberships will need a write protocol or these columns become incorrect. |
| E6 | P3 | `staff.name` duplicates `users.name`. Multi-branch display and payroll will diverge unless the service layer copies on update. |

V1 primary keys and snapshot columns are stable enough for the reserved future tables. That matches design §12.5.

---

## 9. Seeders

| Requirement | Result |
|---|---|
| Seed `ADMIN`, `RECEPTIONIST`, `STAFF` | Yes, idempotent |
| Seed at least one active admin + `user_roles` | Yes (`admin@salon.local`) |
| Sample catalog / staff | Extra vs design §11 (which called those operational). Acceptable for local/dev; passwords are env-driven; production rejects default passwords |

Seed does not create customers, appointments, or financial rows. Good.

---

## 10. Inherited design risks still in the implementation

These are **not** implementation defects versus `Database_Design.md`. They remain true in the running schema because the P0/P1 recommendations in `Database_Review_Report.md` were not approved.

| Prior ID | Still in code? | When it becomes blocking |
|---|---|---|
| P0-S1 Double-booking (no GiST exclusion) | Yes | First concurrent `POST /appointments` |
| P0-S2 Soft delete on invoices/payments/commissions/tips | Yes | First void/reissue of an invoice or payment |
| P1 No `staff_time_off` / closures | Yes | Availability engine |
| P1 Payments not tied to invoice | Yes | Billing Module 7 |
| P1 Refunds are positive `REFUNDED` rows | Yes | Revenue reports |
| P1 No payment idempotency / provider reference | Yes | Card/UPI |
| P2 `branch_id` without parent | Yes | Multi-branch migration |
| P2 No appointment `version` | Yes | Concurrent status edits |

Do not re-implement those as silent model changes. Either accept application-layer enforcement with documented race windows, or approve a follow-up migration.

---

## 11. Recommended next actions (no code in this pass)

**Before Module 1 (Auth)**

1. Apply `alembic upgrade head` against PostgreSQL and confirm the live catalog matches this report.
2. Run seeders in development only.
3. When writing repositories, always filter `is_deleted = false` and `selectinload` many-to-one parents (R1).

**Before Module 6 (Appointments)**

4. Decide whether overlap stays application-only or a GiST exclusion is added.
5. Decide duplicate services: keep unique, or add `quantity`.
6. Add `staff_time_off` if the availability engine must respect leave/holidays.

**Before Module 7 (Billing)**

7. Revisit financial soft delete, `payments.invoice_id`, refund linkage, and payment idempotency.
8. Add the two dashboard indexes in §5.2 if reports ship in the same release.

**When multi-branch starts**

9. Create `branches`, backfill or keep `NULL`, then add FKs. Prefer forbidding non-null `branch_id` until that table exists.

---

## 12. Summary scorecard

| Area | Score | Comment |
|---|---|---|
| Relationships | Pass | Cardinality matches ERD; async lazy-load is the main ORM caveat |
| Foreign keys | Pass | All V1 business FKs present; Restrict; no cascade |
| Indexes | Pass with gaps | Table spec met; dashboard §8 missing two indexes |
| Constraints | Pass vs approved spec | CHECKs and partial uniques are complete; booking/money rules remain application-only |
| Migration | Pass | `0002` is a faithful DDL of the models |
| Future extensibility | Pass with watch-outs | `branch_id` and snapshots are the right hooks; orphan `branch_id` and payment↔invoice coupling are the main later costs |
| Alignment to unapproved P0 review | Not applied | Correct given prior instruction; still a product risk |

**Overall.** Implementation is faithful to the approved V1 schema. Integrity holes that remain are inherited from that schema, plus two dashboard index misses and async relationship loading. No code was changed in this pass.
