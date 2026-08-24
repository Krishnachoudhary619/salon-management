# Database Review Report

**Role.** Principal Backend Architect  
**Date.** 2026-08-24  
**Scope.** `Salon_Backend_Blueprint.md`, `Salon_Backend_Architecture.md`, `Database_Design.md`, `ERD.md`  
**Action.** Review only. No schema, code, or document updates in this pass.

---

## 1. Verdict

The V1 model is **directionally correct** and aligned with the blueprint: UUID keys, audit + soft delete, snapshots for price/commission, one staff per appointment, payments as an audit trail, and reserved `branch_id` / inventory / membership shapes.

It is **not yet production-safe for booking or money**.

The two risks that will cause real salon incidents are:

1. **Double-booking.** Overlap is an application check on split `DATE` + `TIME`. PostgreSQL cannot enforce a non-overlapping range as specified. Two concurrent `POST /appointments` will both pass.
2. **Financial mutability and ambiguous revenue.** Invoices and payments can be soft-deleted and recreated. Refunds are positive `REFUNDED` rows that revenue queries do not subtract. “Today’s revenue” uses `payments.paid_at` (UTC) while the calendar uses `appointments.appointment_date` (local). Those will disagree around midnight and after refunds.

Fix the P0/P1 items before implementing Appointments and Billing. Do not wait until Module 6/7 to discover them.

---

## 2. Severity scale

| Severity | Meaning |
|---|---|
| **P0** | Will cause data corruption, double-booking, or wrong money in V1 |
| **P1** | Should be resolved before production; high operational or audit risk |
| **P2** | Correctness or scale issue that will hurt within months |
| **P3** | Design smell or future-module debt; not blocking V1 if documented |

---

## 3. What is solid (keep)

- UUID primary keys, `NUMERIC` money, `TIMESTAMPTZ` audit timestamps.
- `appointment_services` snapshots (`price`, duration, name) — catalog edits will not rewrite history.
- `commissions` store `service_revenue`, `commission_percentage`, and `commission_amount` instead of recomputing later.
- Partial unique indexes on email / phone / invoice number so soft-deleted values can be reused.
- `refresh_tokens` hashed, rotatable, and revocable — required by logout/refresh and missing from the blueprint tables list (good addition).
- ERD cardinality matches `Database_Design.md` (1–0..1 invoice/commission, 1–N payments/tips).
- Architecture-mandated `branch_id` is present on staff, customers, appointments, payments.
- Dashboard correctly declared as aggregates, not stored KPI tables.
- No `ON DELETE CASCADE` on business data.

---

## 4. Schema issues

### P0-S1 — Appointment overlap cannot be enforced

**Evidence.** `appointments` stores `appointment_date DATE` + `start_time TIME` + `end_time TIME`. Overlap is a service-layer rule. The listed index is a B-tree on `(staff_id, appointment_date, start_time, end_time)`.

**Problem.** B-tree indexes do not express “ranges must not overlap.” There is no `tstzrange` / `tsrange` and no `EXCLUDE USING gist`. Two requests that read “slot free” then insert will both commit.

**Impact.** Double-booking. This is the core product failure mode.

**Recommendation.** Add a stored range (generated is fine):

- `time_range tsrange` or `tstzrange` from date + start/end
- `EXCLUDE USING gist (staff_id WITH =, time_range WITH &&) WHERE (is_deleted = false AND status NOT IN ('CANCELLED', 'NO_SHOW'))`

Keep `DATE`/`TIME` columns if the API wants them. Do not rely on them alone for integrity.

### P0-S2 — Soft delete on financial documents

**Evidence.** `invoices`, `payments`, `commissions`, and `tips` all have `is_deleted` / `deleted_at`. Invoice uniqueness is `appointment_id WHERE is_deleted = false`.

**Problem.** Soft-deleting an invoice unlocks a second invoice for the same appointment. Soft-deleting a `SUCCESS` payment changes whether the appointment is “paid” and whether commission should exist. That is not an audit trail; it is a rewrite of history.

**Impact.** Duplicate invoices, vanished payments, commissions that no longer match cash, failed tax audits.

**Recommendation.** Financial rows are append-only. Void with a new row or a `VOIDED` / `REFUNDED` status. Do not soft-delete invoices, payments, or commissions. If a row must be hidden from UI, use `voided_at`, not `is_deleted`.

### P1-S3 — No exception calendar

**Evidence.** Availability uses only weekly `staff_schedules`. No holiday, leave, or one-off closure table.

**Problem.** The engine will allow bookings on Diwali, staff sick days, and salon closures.

**Recommendation.** Add `staff_time_off` (staff_id, date or range, reason) and optionally `salon_closures` before the availability engine is considered complete.

### P1-S4 — `DATE` + `TIME` has no timezone

**Evidence.** Design principle 7: local date/time; multi-branch will use `branches.timezone`. Payments and audit use `TIMESTAMPTZ`.

**Problem.** “Today” for a booking and “today” for cash are different types. A 00:30 IST payment is still “yesterday” in UTC. After multi-branch, two salons in different zones cannot share a naive `DATE` without a timezone.

**Recommendation.** Persist `starts_at` / `ends_at` as `TIMESTAMPTZ` (derived). Keep local date/time as display/query helpers. All revenue windows must filter `paid_at` in the salon timezone, not raw UTC day boundaries.

### P1-S5 — Conflicting rule on duplicate services

**Evidence.** `appointment_services` unique `(appointment_id, service_id)` vs the note “if two identical services are required, drop this unique.”

**Problem.** Two Hair Cuts on one ticket is a real salon case (two people, or two services of the same catalog item). The unique constraint forbids it; the note says maybe not.

**Recommendation.** Decide now: add `quantity INTEGER CHECK (quantity > 0)` and keep the unique, **or** drop the unique and allow two lines. Do not leave this open until implementation.

### P1-S6 — Invoice has no line items and no lock on source lines

**Evidence.** Invoice header stores `subtotal` / `tax` / `total`. Lines live on `appointment_services`. Soft-deleting a line after invoicing is allowed by the table rules (“recalculate end_time if still reschedulable”).

**Problem.** After `COMPLETED`, lines can still change while the invoice is declared immutable. Totals diverge with no database check.

**Recommendation.** Once an invoice exists, reject mutations to that appointment’s service lines (status check + maybe `invoiced_at` on the appointment). Optionally copy lines onto `invoice_items` so the legal document does not depend on a mutable booking table.

### P1-S7 — Payments do not reference the invoice

**Evidence.** `payments.appointment_id` only. One invoice per appointment is a partial unique, not a hard 1:1 if soft delete is kept.

**Problem.** A payment is not tied to a specific invoice version. Settlement, reprints, and voids become ambiguous.

**Recommendation.** Add `payments.invoice_id` → `invoices.id` (NOT NULL once an invoice exists, or required for `SUCCESS`).

### P1-S8 — Refunds are poorly modeled

**Evidence.** “V1 records a `REFUNDED` row referencing the same appointment” with `amount > 0`. Revenue = `sum(SUCCESS)`.

**Problem.** A ₹1000 SUCCESS + ₹1000 REFUNDED still reports ₹1000 revenue. There is no `original_payment_id`, no signed amount, no remaining-balance column.

**Recommendation.** Add `original_payment_id`. Treat refunds as negative cash in reporting (`SUCCESS - REFUNDED`) or store `amount` signed. Never let a refund look like extra takings.

### P1-S9 — No payment idempotency or gateway reference

**Evidence.** Payments have method, status, amount, `paid_at`. No `idempotency_key`, `provider`, or `provider_reference`.

**Problem.** Double-submit on UPI/card creates two `SUCCESS` rows. The appointment looks overpaid. Settlement files cannot be matched.

**Recommendation.** Add nullable `provider_reference` (unique where not null) and `idempotency_key` (unique per appointment or globally). Required before any non-cash tender.

### P1-S10 — Dual lifecycle on tokens and users

**Evidence.** `users` has `is_active` and `is_deleted`. `refresh_tokens` has `revoked_at`, `expires_at`, and soft delete.

**Problem.** Four ways to be “dead.” Queries will miss a case. Token table will grow forever (30-day refresh × every login).

**Recommendation.** Users: `is_active` for disable, soft delete for removal — document the exact login predicate. Tokens: `revoked_at` + `expires_at` only; purge expired rows. Do not soft-delete tokens.

### P2-S11 — `branch_id` without a parent

**Evidence.** Nullable UUID, “no FK in V1,” on many tables.

**Problem.** A typo UUID will sit in production until `branches` exists, then `ADD CONSTRAINT` will fail.

**Recommendation.** Either seed a single `branches` row in V1 and FK now, or constrain `branch_id IS NULL` in V1 (`CHECK (branch_id IS NULL)`). Do not accept orphan UUIDs.

### P2-S12 — `staff.name` vs `users.name`

**Evidence.** Staff “may mirror `users.name`.”

**Problem.** Two sources of display name. Reception and payroll will disagree.

**Recommendation.** Staff display name is either always copied on user update, or staff does not store `name` and reads `users.name`.

### P2-S13 — No optimistic lock on appointments

**Evidence.** Status transitions are application rules only. No `version` / `xmin` strategy documented.

**Problem.** Two receptionists can move the same appointment to `ARRIVED` and `CANCELLED`. Last write wins.

**Recommendation.** Add `version INTEGER` and reject stale updates.

### P3-S14 — Soft delete applied too broadly

Junction rows (`user_roles`) and seed tables (`roles`) do not need the same soft-delete machinery as customers. Soft-deleting `roles.name = ADMIN` then inserting a new ADMIN creates a second role UUID while old `user_roles` still point at the old row.

**Recommendation.** Keep soft delete on operational entities. Roles: no delete. `user_roles`: hard delete or unique without soft delete.

---

## 5. Normalization issues

The schema is roughly 3NF for booking. The problems are **controlled denormalization without a single writer** and **document vs line split**.

| Issue | Form | Risk | Recommendation |
|---|---|---|---|
| `customers.visit_count`, `total_spent`, `last_visit` | Denormalized aggregates | Drift on refund, void, or failed job. CRM list lies. | Keep for list performance **or** drop and aggregate. If kept: update in the same transaction as invoice/payment; define refund behavior (decrement or not). Add a reconciliation query in ops. |
| `invoices.subtotal` vs sum of snapshots | Denormalized header | Diverges if lines change after invoice | Lock lines after invoice; optional `invoice_items` |
| `staff.name` / `users.name` | Redundant attribute | Inconsistent UI | One source of truth |
| `commissions.staff_id` independent of `appointments.staff_id` | Missing constraint | Commission paid to the wrong person | `CHECK` via trigger: `commissions.staff_id = appointments.staff_id` in V1 |
| `commissions.commission_amount` vs formula | Derived attribute stored | Silent math error | Trigger or generated column from revenue × percent (rounding rule documented) |
| Invoice header without lines | 1NF document model | Legal copy depends on booking table | Copy lines at invoice time |
| Future `product_stock.quantity_on_hand` without movements | Mutable balance | Unauditable inventory | When inventory ships, stock changes only via a movement ledger |

None of these require a rewrite of table names. They require **constraints and a write protocol**.

---

## 6. Missing indexes

Existing indexes are a good start. These gaps matter.

| Gap | Why | Suggested index |
|---|---|---|
| Appointment overlap is B-tree only | Cannot enforce or efficiently search ranges | GiST on `(staff_id, time_range)` partial |
| `appointments (staff_id, completed_at, status)` | Promised in §8 for top staff; **not** listed on the table | Partial: `WHERE is_deleted = false AND status = 'COMPLETED'` |
| `customers (created_at)` | Promised in §8 for customer growth; **missing** on `customers` | `(created_at) WHERE is_deleted = false` |
| Most `is_deleted` indexes are single-column | Planner rarely uses a boolean index alone | Prefer **partial** indexes `WHERE is_deleted = false` on the real filter columns |
| `payments` revenue | `(paid_at, payment_status)` includes failed rows and deleted rows | `(paid_at) WHERE payment_status = 'SUCCESS' AND is_deleted = false` (or after dropping soft delete) |
| `invoices (created_at)` | Not partial | `(created_at) WHERE is_deleted = false` |
| `tips (created_at)` / `commissions (created_at)` | Period reports also filter time; staff+created_at exists, global day rollup does not | `(created_at)` or `(created_at, staff_id)` |
| `appointment_services (appointment_id)` | Should be partial if soft delete remains | `(appointment_id) WHERE is_deleted = false` |
| Login path | `users` has email unique; add covering `is_active` in the unique predicate | Unique on `lower(email) WHERE is_deleted = false AND is_active = true` is optional; at least document the login filter |
| Token purge | `expires_at` exists; good | Add scheduled delete; consider BRIN on `expires_at` only if the table grows huge |

**UUID v4 primary keys.** Random inserts fragment B-trees. Fine for a single salon for years. If you ever multi-branch with high write volume, switch new tables to UUIDv7. Not a V1 blocker.

---

## 7. Missing constraints

Application checks are not a substitute for these.

| Missing constraint | Table | Why it matters |
|---|---|---|
| Exclusion / no-overlap | `appointments` | Double-booking |
| Exclusion / no-overlap | `staff_schedules` | Two windows 10–13 and 11–14; design says “optional.” It should not be optional. |
| `CHECK ((is_deleted = false AND deleted_at IS NULL) OR (is_deleted = true AND deleted_at IS NOT NULL))` | All soft-delete tables | Half-deleted rows |
| `CHECK ((status = 'CANCELLED') = (cancelled_at IS NOT NULL))` | `appointments` | Status vs timestamp drift |
| `CHECK ((status = 'COMPLETED') = (completed_at IS NOT NULL))` | `appointments` | Same |
| `CHECK (phone ~ '^[0-9]{10,15}$')` | `customers`, `staff` | Architecture requires 10–15 digits |
| Commission staff matches appointment staff | `commissions` | Wrong earner |
| `commission_amount = round(service_revenue * commission_percentage / 100, 2)` | `commissions` | Stored math must match |
| Invoice exists only if appointment is `COMPLETED` | `invoices` | Trigger or status gate |
| `SUCCESS` payment forbidden when appointment is `CANCELLED` / `NO_SHOW` | `payments` | Trigger; architecture rule is not in SQL |
| `tips` forbidden on cancelled appointments | `tips` | Same |
| `invoice_number` allocation | `invoices` | No sequence; two completions can collide on `INV-20260824-0001` before the unique check retries |
| `version` / row lock | `appointments` | Lost status updates |
| `branch_id IS NULL` in V1 **or** FK to `branches` | Several | Orphans |
| Financial tables: no soft delete | invoices / payments / commissions | See P0-S2 |
| `original_payment_id` on refunds | `payments` | Audit |
| At least one service line | `appointments` | Deferred constraint or service-only; DB currently allows an empty appointment |

`end_time > start_time` is present and good. `total = subtotal + tax` is present and good. `SUCCESS` implies `paid_at` is present and good.

---

## 8. Scalability concerns

A single salon will not hit PostgreSQL limits in V1. The design still has structural scale traps.

1. **Hot availability path.** Every booking reads schedules + overlapping appointments for a staff/day, then writes. Without a GiST exclusion and a short row lock on `staff` (or the day’s appointments), this path is racy and will get slower as history grows. Always qualify overlap queries with `appointment_date` (or the range) and `is_deleted = false`.

2. **Unbounded token table.** Daily login × 30-day expiry with no purge will become the largest table in a quiet salon. Add retention.

3. **Random UUID indexes** on high-write tables (`appointments`, `payments`, `refresh_tokens`). Acceptable now; plan UUIDv7 if write rate jumps.

4. **Global unique phone on customers.** Works for one CRM identity. If two branches later want isolated guest books, this unique must become `(phone, branch_id)` and merge tooling will be required. Call this out before selling multi-branch.

5. **No partitioning story.** Not needed until millions of appointments. When it is needed, partition `appointments` and `payments` by month on a `TIMESTAMPTZ` column — another reason to store `starts_at` / `paid_at` as timestamptz, not split date/time.

6. **`SELECT *` style dashboard risk.** The architecture forbids in-memory totals. The schema does not include a reporting replica or materialized daily rollup. That is fine until a manager opens “revenue by day” for 24 months on the primary during peak hours.

7. **N+1 is an ORM problem**, not a schema problem. The ERD is join-friendly (`appointment_id` on every child). Keep it that way; do not add more denormalized counters to avoid joins.

---

## 9. Reporting bottlenecks

Architecture metrics: revenue today/month, appointments today, customers served, average ticket, top staff. Design §8 maps them to tables. The mapping is **internally inconsistent**.

| Metric | Documented source | Problem |
|---|---|---|
| Revenue today / month | `sum(payments.amount) WHERE SUCCESS` | Ignores refunds. Uses `paid_at` UTC, not salon local date. Soft-deleted payments disappear from history. |
| Average ticket | `avg(invoices.total)` | Invoice exists on `COMPLETED`, possibly **before** payment. Unpaid completions inflate ticket count. Tax included or not is undefined. |
| Appointments today | `appointment_date` | Local date. Will not match revenue “today.” |
| Customers served | Distinct `customer_id` on `COMPLETED` | Includes unpaid completions. Does not use `customers.visit_count` (which can drift). |
| Top staff | Appointments + invoice/payment join | `payments` and `invoices` have **no `staff_id`**. Join must go `payment → appointment → staff`. Easy to get wrong if `commissions.staff_id` is used instead and they diverge. |
| Customer growth | `customers.created_at` | Auto-create on booking means “growth” is “first booking,” not “first visit completed.” Decide which KPI you want. |

**Missing report indexes** are listed in §6. The larger issue is **no single grain for “a sale.”**

A sale should be one immutable fact, for example:

```text
completed appointment
  + issued invoice
  + net cash (SUCCESS amounts - REFUNDED amounts)
  + staff_id from the appointment
  + local business date
```

Until that is defined, every dashboard card can be “correct” against a different table and the owner will not trust the numbers.

**`customers.total_spent` vs reports.** List views will show the counter; dashboard will sum payments. After a refund they will disagree unless both paths share one function.

**No as-of reporting.** There is no period lock. Backdating `paid_at` or completing yesterday’s appointment today rewrites last month’s dashboard with no audit of the change (status history is not stored).

---

## 10. Financial data issues

This is the weakest part of the design relative to the architecture’s own payment/commission rules.

1. **Two revenue books.** Cash received (`payments`) vs billed (`invoices`). The design says both, for different cards. That is valid **only if** product copy says so. If both cards are labeled “revenue,” they will not match (unpaid completed work, overpay, refunds, tax).

2. **Overpay is allowed; change is not stored.** Cash ₹1000 on a ₹870 invoice looks like ₹1000 revenue. Need `amount_tendered` / `change_given` or cap recognized revenue at `invoice.total`.

3. **Tax is an amount with no rate, inclusive/exclusive flag, or jurisdiction.** Acceptable for a prototype. Not acceptable if you print GST invoices in India. Add `tax_rate_snapshot` and `tax_inclusive` before going live with invoices.

4. **No currency.** Implicit INR. Add `currency CHAR(3)` default `'INR'` on invoices and payments now; it is cheaper than a rewrite.

5. **Commission trigger vs unpaid completion.** Architecture: COMPLETED **and** SUCCESS. Design §7.2 creates the invoice on COMPLETED, then waits for payment, then commission. Good. There is no row that says “awaiting payment.” Reception can complete, never collect, and still see the appointment in “customers served.”

6. **Commission base is pre-tax service snapshots.** Confirm tax is not in `price_snapshot`. If catalog prices are tax-inclusive, commission is taken on tax. That must be an explicit rule.

7. **Tips are not cash-accounted.** A tip can be recorded with no payment row. Performance reports will show tip income that never hit the drawer.

8. **No idempotency / acquirer id** — see P1-S9. You cannot close a card batch.

9. **Immutable commissions, mutable payments.** If a payment is soft-deleted or refunded, the commission row remains. Staff is overpaid on paper. There is no clawback row.

10. **`NUMERIC(12,2)` rounding** is unspecified (`half_up` vs `half_even`). Two application instances can persist different `commission_amount` values for the same inputs unless the database computes it.

11. **Invoice numbers are application-generated.** Under concurrency the unique index will throw; that is OK if the app retries. A `SEQUENCE` or date-scoped sequence is safer.

12. **No link from payment to invoice** — see P1-S7.

---

## 11. Document consistency

| Topic | Blueprint | Architecture | Database_Design | ERD | Assessment |
|---|---|---|---|---|---|
| UUID PK, audit, soft delete | Audit only; soft delete “preferred” on staff | Required on all business tables | Applied to **all** tables including finance and tokens | Matches design | Over-applied on finance |
| `branch_id` | Not in table lists | staff, customers, appointments, payments | Those plus extras | Reserved FKs | Aligned; extras are fine |
| Refresh tokens | Not listed | Login + refresh APIs | Table exists | Shown | Correct extension |
| Appointment columns | No cancelled/completed timestamps | Status rules only | Added `cancelled_at`, `completed_at` | Keys only | Good extension; constraints missing |
| Invoice after completion | Yes | Yes | Yes | 1–0..1 | Aligned |
| Payment >= invoice | Implied | Yes | Yes, plus overpay | — | Overpay side effects not designed |
| Commission on COMPLETED + SUCCESS | Yes | Yes | Yes | 1–0..1 | Aligned; no SQL enforcement |
| Dashboard = SQL aggregates | Yes | Yes | Yes, but two fact sources | — | Metric grain unresolved |
| Inventory / memberships | Future | Relations only | Reserved tables | Future ERD | Adequate placeholder; stock without ledger is weak |
| Status change logging | — | Log status changes | No history table | — | Gap |

ERD matches the design’s cardinality. It does not need changes until the schema issues above are decided.

---

## 12. Recommended V1 fix set (do not implement in this pass)

Do these before Appointments / Billing code:

1. Add a stored appointment time range + GiST exclusion (P0-S1).
2. Remove soft delete from `invoices`, `payments`, `commissions` (P0-S2). Use void/refund rows.
3. Add `invoice_id` on payments; model refunds with `original_payment_id` and net-cash reporting.
4. Add payment `idempotency_key` / `provider_reference`.
5. CHECK phone format; CHECK cancelled/completed timestamps vs status; CHECK commission staff = appointment staff; CHECK commission math.
6. Exclusion constraint on `staff_schedules` for the same staff/day.
7. Define one reporting grain: net successful payments in salon local time, ticket = paid invoices only (or document two labels).
8. Partial indexes listed in §6; add the two indexes promised in design §8 but missing on the tables.
9. Either seed `branches` now or `CHECK (branch_id IS NULL)`.
10. Decide duplicate-service / quantity now.

Do these before calling the availability engine done:

11. `staff_time_off` / salon closures.
12. Persist `starts_at`/`ends_at` timestamptz.

Do these before real card/UPI or GST:

13. Currency, tax rate snapshot, tax inclusive flag.
14. Invoice line copy or hard lock on appointment lines after invoice.
15. Rounding rule in the database.

---

## 13. Out of scope (not defects)

- Missing expense, payroll, loyalty, and notification tables — correctly deferred.
- Permissions stored in application code — acceptable for three roles.
- Customers not being users — matches V1.
- Dashboard having no tables — correct.

---

## 14. Close

Approve the **shape** of the model. Do not approve the **integrity story** for booking or money.

Next step, when you want it: apply the P0/P1 decisions back into `Database_Design.md` and `ERD.md` only. Still no models or migrations until that revision is accepted.
