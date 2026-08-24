# Backend Audit Report

**Role.** Principal Backend Architect  
**Date.** 2026-08-24  
**Scope.** `backend/app/**`, `backend/tests/**`, `Salon_Backend_Architecture.md`, `Salon_Backend_Blueprint.md`, `Database_Design.md`  
**Action.** Review only. No code changes in this pass.

---

## 1. Verdict

The V1 backend is a **complete, layered FastAPI system**. All blueprint modules (auth through team performance) exist. Routers are thin, services own domain rules, repositories own SQL, responses use the standard envelope, and **169 tests** cover unit plus integration paths.

It is **not production-ready for concurrent booking or money**.

The three issues that will cause salon incidents are:

1. **Double-booking.** Availability is a read-then-insert check with no row lock and no exclusion constraint. Two concurrent `POST /appointments` can both commit.
2. **Access tokens outlive account changes.** Protected routes trust JWT `roles` and never re-load the user. Deactivate staff, demote a role, or call logout — the access token still works for up to 30 minutes.
3. **Financial races and overpayment.** Invoice/commission inserts are check-then-insert with no `IntegrityError` handling. Successful payments are not capped at invoice remaining. Refunds exist as an enum value only. Revenue queries do not subtract `REFUNDED`.

Fix the P0/P1 items before a real salon uses this. Layering, RBAC matrix shape, validation style, and SQL aggregations for dashboard/performance are already in good shape.

---

## 2. Severity scale

| Severity | Meaning |
|---|---|
| **P0** | Data corruption, double-booking, or wrong money in V1 |
| **P1** | Should be resolved before production; auth, audit, or operational risk |
| **P2** | Correctness or scale issue that will hurt within months |
| **P3** | Smell, docs drift, or future-module debt; not blocking V1 if documented |

---

## 3. What is solid (keep)

- **Clean architecture.** `Router → Service → Repository → Database` is followed. Routers call services and wrap `success_response`. Domain rules (workflow, availability, commission snapshots) live in services/engines.
- **Module layout.** Domain packages include `models.py`, `schemas.py`, `repository.py`, `service.py`, `router.py`, `dependencies.py`. Dashboard and performance correctly have no persisted tables.
- **Identity model.** UUID PKs, audit mixins, soft delete, optional `branch_id` on the architecture-mandated tables.
- **API contract.** `/api/v1` prefix, `{success, message, data/errors}` envelope, pagination `page/limit/search/sort_by/sort_order` with `MAX_LIMIT=100`, list endpoints return `{items, total, page, limit}`.
- **Auth primitives.** bcrypt password hashes, refresh tokens stored as SHA-256, rotation with reuse detection (revoke all on reuse), login/logout/refresh/`/me`, structured logs with secret redaction.
- **RBAC shape.** ADMIN / RECEPTIONIST / STAFF with a permission enum. Own-resource scoping for appointments, commissions, tips, tasks, and performance is implemented in services, not only at the router.
- **Booking rules.** Status workflow matches architecture (cannot complete before arriving; terminal states cannot be edited; availability checked on create/reschedule). Line items snapshot name, duration, and price.
- **Money snapshots.** Commissions store `service_revenue`, `commission_percentage`, and `commission_amount`. Tips are separate from commission.
- **KPI queries.** Dashboard and performance use SQL `GROUP BY` / `SUM` / `COUNT(DISTINCT)`, not Python scans of full tables.
- **Relationship loading.** List/detail repositories use `selectinload` plus `noload` on inverse collections so listing staff or appointments does not pull entire graphs.
- **Tests.** Every business module has unit and integration tests. Auth, booking, billing, commissions, tips, tasks, dashboard, and performance are exercised.

---

## 4. Architecture compliance

### Aligned

| Standard | Implementation |
|---|---|
| Layering | Routers have no SQL and almost no branching beyond permission deps |
| Naming | `StaffService` / `StaffRepository`, snake_case plural tables |
| Auth | JWT access + refresh, `Depends` on protected routes |
| Envelope | Central handlers for `AppException`, `RequestValidationError`, `HTTPException` |
| Pagination | Shared `PaginationParams` on list routes |
| Logging | Structured `structlog`; login, appointment, payment, status changes logged; passwords/tokens redacted |
| Swagger | `/docs` and `/redoc`; most endpoints have summary, description, tags |
| Future fields | `branch_id` on staff, customers, appointments, payments (and extra tables) |
| Development order | Phases 1–4 are present, including Team Performance |

### Gaps

| ID | Severity | Finding |
|---|---|---|
| A1 | P3 | Architecture folder tree lists `users/` as a full module. `app/users/` is models only (no schemas/service/router). Users are created as a side effect of staff. Acceptable for V1 if documented; the architecture file is stale. |
| A2 | P3 | Architecture tree omits `performance/`. The module exists and is mounted. Docs lag the code. |
| A3 | P3 | Architecture §16 says “Payment amount >= invoice total.” The code allows split payments (reasonable) and also **overpayment** (not reasonable). The written rule and the implementation disagree. |
| A4 | P3 | `backend/README.md` still says the package is “foundation layer only.” Misleading for operators. |
| A5 | P3 | A few GET/PUT routes lack `description` (`GET /appointments/{id}`, `GET /staff-schedules/{id}`, `PUT /staff-schedules/{id}`). Architecture requires summary + description + tags. |
| A6 | P2 | Receptionist cannot `GET /staff` (`STAFF_READ` is admin-only) and schedule payloads have `staff_id` but no name. Front desk cannot build a staff picker from the API as specified. They can book if they already know UUIDs. |
| A7 | P3 | Unused architecture leftovers: `Permission.USER_READ` / `USER_WRITE` / `REPORTS_READ` / `COMMISSION_CONFIG` are never attached to routes. Commission edits use `actor.is_admin` instead of `COMMISSION_CONFIG`. `ensure_owner_or_admin` and `get_current_user_optional` are unused. |

---

## 5. RBAC

### Matrix vs code

| Role | Architecture | Code | Notes |
|---|---|---|---|
| ADMIN | Everything | `frozenset(Permission)` | Correct |
| RECEPTIONIST | Customers, appointments, schedules. No reports, no commission config | Also payments, invoices, tips (read/write). No staff CRUD, dashboard, performance, commissions, tasks | Front-desk money access is a **sensible extension** of the blueprint billing module. Staff roster read is **missing** for booking UX (A6) |
| STAFF | Own appointments, earnings, tasks. No customer list, no reports, no staff management | `SERVICE_READ`, own appointments, own commissions/tips/tasks, `PERFORMANCE_READ_OWN` | Catalog read is required to book. Team `/performance/team` correctly denied |

Own-resource checks are consistent in appointments, commissions, tips, tasks, and performance: full permission → unscoped; otherwise `staff.user_id = actor.id`. Reassignment of tasks is admin-only. Commission percentage updates require admin.

### Issues

| ID | Severity | Finding |
|---|---|---|
| R1 | P1 | **JWT is the source of truth for permissions.** `require_permissions` depends on `app.common.dependencies.get_current_user`, which decodes the access token and never hits the database. `app.auth.dependencies.get_current_user` *does* reload the user, refresh roles, and reject inactive accounts — but only `/auth/me` uses it. After deactivate, role change, or soft-delete, the access token retains old roles until expiry. |
| R2 | P1 | **Logout does not invalidate access tokens.** Logout revokes refresh rows only. Combined with R1, a stolen or leftover Bearer token works until `ACCESS_TOKEN_EXPIRE_MINUTES`. |
| R3 | P2 | **Staff can create CRM customers** via `AppointmentCreateRequest.customer` → `CustomerService.get_or_create_by_phone`. Router permission is `APPOINTMENT_WRITE_OWN`, not `CUSTOMER_WRITE`. Architecture: staff cannot access the customer list; they can still write customers. Staff can also book any `customer_id` UUID without `CUSTOMER_READ`. |
| R4 | P2 | Staff with `APPOINTMENT_WRITE_OWN` can walk a booking to `COMPLETED`, which generates an invoice. They cannot record payment. That may be intended floor workflow; it is not stated in the architecture. |
| R5 | P3 | Commission config is gated with `actor.is_admin` in `StaffService.update_staff`, not `Permission.COMMISSION_CONFIG`. Harmless while only ADMIN exists; the permission is dead code. |

---

## 6. Security

| ID | Severity | Finding |
|---|---|---|
| S1 | P1 | Dual `get_current_user` (R1). Treat as the primary auth defect. Wire `require_permissions` to the auth dependency that loads `User.is_active` and live roles. |
| S2 | P1 | No login rate limiting or lockout. `/auth/login` is a brute-force target. bcrypt helps but does not replace throttling. |
| S3 | P2 | User enumeration: unknown email → `"Invalid email or password"`; disabled account → `"Account is disabled"`. `user is None` also skips `verify_password`, which is a timing oracle. |
| S4 | P2 | Password policy is `min_length=1`, `max_length=72`. Staff create and login accept `"x"`. No complexity rules. |
| S5 | P2 | Default `CORS_ORIGINS=*`. Production JWT weak-secret check exists; there is no equivalent “CORS must not be `*` in production.” OpenAPI `/docs` and `/redoc` stay enabled in production. |
| S6 | P2 | JWT has no `iss` / `aud`. Algorithm is HS256 (fine for a single service). `JWT_SECRET` production check only rejects known placeholder prefixes, not low entropy. |
| S7 | P2 | `database_url` interpolates `DB_PASSWORD` without URL-encoding. A password containing `@`, `:`, or `/` breaks the DSN or changes the parsed user/host. |
| S8 | P2 | Unhandled exceptions in `DEBUG` return `str(exc)` to the client (`exception_handlers.py`). Ensure `DEBUG=false` in production. No `TrustedHostMiddleware`. |
| S9 | P3 | Client-supplied `X-Request-ID` is accepted as-is into logs. Prefer generating server-side IDs, or allowlisting a UUID pattern. |
| S10 | P3 | Health is liveness only (`{"status": "ok"}`) and does not check the database. Add a separate readiness probe before Kubernetes/Docker rely on `/health`. |
| S11 | P3 | Seed admin/staff passwords live in settings. Seed skips extra sample staff in production; default admin seed should also be impossible when `APP_ENV=production` unless explicitly opted in. |

What is already good: parameterized SQLAlchemy (no string-built queries), ILIKE search escaping of `%`/`_`, bcrypt 72-byte cap, refresh-token hash at rest, token-type check (`access` vs `refresh`), sensitive log key redaction.

---

## 7. Validation

Request bodies use Pydantic v2 with `extra="forbid"` on write DTOs. Phone (10–15 digits), `EmailStr`, `gt=0` on prices/durations/payment amounts, schedule `end_time > start_time`, appointment duplicate `service_ids` rejected, date windows capped (calendar 42 days, dashboard/performance 366 days).

| ID | Severity | Finding |
|---|---|---|
| V1 | P2 | Weak passwords (S4). Same gap on `StaffCreateRequest.password`. |
| V2 | P2 | `PaymentCreateRequest` allows any positive amount and does not validate remaining balance. Split pay is OK; paying ₹400 twice on a ₹400 invoice is accepted. |
| V3 | P2 | `PaymentStatus.REFUNDED` cannot be created (`"Refunds cannot be created through this endpoint"`) and there is no refund API. The enum and DB check constraint advertise a flow that does not exist. |
| V4 | P3 | Staff/customer phone validators are copy-pasted (`_PHONE_PATTERN` in two schemas). Drift risk, not a current bug. |
| V5 | P3 | Query params on `/health` are ignored (test asserts 200). Harmless. |
| V6 | P3 | Money rounding is inconsistent: billing `_money` uses default `quantize` (banker's rounding); commissions/dashboard/performance use `ROUND_HALF_UP`. ₹10.00 × 33.35% is already tested as half-up in commissions; billing totals may disagree by a paisa on odd splits. |

---

## 8. Transactions

`get_db` is a correct request-scoped unit of work: yield session, `commit` on success, `rollback` on exception. Services `flush` rather than commit, so complete → invoice → payment → commission → customer visit **can** share one transaction per request. That part is right.

| ID | Severity | Finding |
|---|---|---|
| T1 | P0 | **Appointment overlap is not transactional.** `AvailabilityEngine.validate_slot` reads busy intervals, then `AppointmentRepository.create` inserts. No `SELECT … FOR UPDATE`, no `pg_advisory_xact_lock(staff_id)`, no `EXCLUDE USING gist` on a time range. Two concurrent bookings for Priya 10:00–10:30 both pass. This is the same P0 as `Database_Review_Report.md` P0-S1; the application did not close it. |
| T2 | P1 | **Invoice generate is check-then-insert.** Unique partial index `uq_invoices_appointment_id_active` exists on PostgreSQL, but there is no `IntegrityError` → `ConflictException` mapping. Concurrent `COMPLETED` transitions become HTTP 500. SQLite tests do not enforce `postgresql_where` unique indexes. |
| T3 | P1 | **Commission generate is the same pattern** (`uq_commissions_appointment_id_active`). Two successful payments crossing the paid-in-full threshold in parallel can 500 or, on SQLite, insert two rows. |
| T4 | P1 | **Customer visit counters are read-modify-write in Python** (`visit_count += 1`, `total_spent += amount`) with no `UPDATE … SET visit_count = visit_count + 1` and no row lock. Concurrent paid-in-full requests can drop a visit. |
| T5 | P1 | **Successful payments are not serialized per appointment.** `sum_successful` then insert has a race: both requests see `paid = 0` and both insert ₹400. Overpay plus duplicate commission/visit side effects. |
| T6 | P2 | Unique constraint failures anywhere become unhandled 500s. Catch `IntegrityError` in the session layer or per write path and map to `ConflictException`. |
| T7 | P3 | Appointment line writes loop `flush` per service. Same transaction, extra round-trips only. |

---

## 9. Performance

Dashboard and team performance follow architecture §19–20: aggregations in SQL, date windows exclusive at the end in UTC, indexes on `(paid_at, payment_status)`, `(staff_id, created_at)` for commissions/tips, `(appointment_date, status)`.

| ID | Severity | Finding |
|---|---|---|
| P-perf1 | P2 | UTC calendar dates vs salon local time. “Today” and “this month” are `datetime.now(UTC).date()`. A 9pm IST visit is already tomorrow in UTC. Dashboard revenue and appointment volume will disagree with the wall clock. Called out previously in the database review. |
| P-perf2 | P2 | `GET /appointments/calendar` loads every appointment in the range (max 42 days) with services, customer, and staff. Fine for one salon; will get heavy with many staff and a dense book. |
| P-perf3 | P3 | `BaseRepository.list` runs `COUNT(*)` over a subquery of the filtered select, then the page query. Correct, two queries. Acceptable. |
| P-perf4 | P3 | Availability slot generation walks 15-minute steps in Python for one staff/day. Cheap. |
| P-perf5 | P3 | Connection pool `pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`. Reasonable defaults; tune when deploying. |

---

## 10. N+1 queries

Eager-load policy on **detail/list of entities** is generally good: appointments, staff, commissions, tips, and tasks `selectinload` what the response needs and `noload` inverse collections (`Staff.appointments`, `Customer.appointments`, etc.). Default `lazy="selectin"` on several model relationships would N+1 if a query forgot `noload`; repositories currently remember.

Real N+1 is in **billing list endpoints**:

| ID | Severity | Finding |
|---|---|---|
| N1 | P1 | `BillingService.list_invoices`: for **each** invoice, `sum_successful(appointment_id)` then `get_detail(invoice.id)`. 1 + 2N queries per page (up to 100). `get_detail` re-loads appointment + lines already skippable if `list` used `_detail_stmt` and a single grouped `SUM(payments)` join. |
| N2 | P1 | `BillingService.list_payments`: for **each** payment, `invoice_repository.get_by_appointment_id`. 1 + N queries. Join invoices once or subquery `invoice_id`. |
| N3 | P3 | `AppointmentService._write_lines` inserts lines one flush at a time (write N+1). Prefer `add_all` + one flush. |
| N4 | P3 | Staff `noload(...)` option blocks are duplicated in seven repositories. Not N+1 today; easy to miss one and reintroduce it. |

Dashboard `top_performers` and performance `staff_metrics` use grouped subqueries / joins — not N+1.

---

## 11. Code duplication

None of these are defects by themselves. They are the places a later bug will be fixed in one module and missed in another.

| Area | Copies | Risk |
|---|---|---|
| `_scoped_staff_id` / `_ensure_can_access` | appointments, commissions, tips, tasks, performance | Own-resource rules drift (already slightly different messages) |
| `_money` / `Decimal("0.01")` | billing, commissions, tips, dashboard, performance | Rounding mode already drifted (V6) |
| UTC date window helpers | `dashboard/service.py`, `performance/service.py` | End-exclusive vs inclusive windows diverge |
| `_PHONE_PATTERN` | staff schemas, customer schemas | Validation drift |
| `noload(Staff.*)` | 7 repositories | Forgotten noload → accidental graph load |
| `_active_lines` | billing, commissions, appointments | — |
| Status workflow maps | `appointments/workflow.py`, `tasks/workflow.py` | Fine as two domains |
| In-memory SQLite app fixture | almost every integration test | Slow to change `get_db` override; consider a shared fixture |

Extracting `app.common.money`, `app.common.dates`, and `app.common.rbac.scope_staff` would shrink this without changing behavior.

---

## 12. Database review items still open

`Database_Review_Report.md` P0/P1 schema issues were **not** applied (by prior instruction). They remain true of the running backend:

- No `tstzrange` + `EXCLUDE` for overlap (T1).
- Soft delete on invoices, payments, commissions, tips (financial history is mutable).
- No leave/holiday calendar; availability is weekly `staff_schedules` only.
- `REFUNDED` payments are not subtracted from dashboard/performance revenue (`payment_status = SUCCESS` only).
- Denormalized `customers.visit_count` / `total_spent` can drift (T4).

---

## 13. Testing vs architecture §21

| Requirement | Status |
|---|---|
| Unit tests per module | Yes |
| Integration tests per module | Yes (auth, staff, services, customers, schedules, appointments, billing, commissions, tips, tasks, dashboard, performance, health) |
| 80% coverage target | Not measured in this pass; 169 tests passing is necessary but not sufficient |
| SQLite vs PostgreSQL | Partial unique indexes and exclusion constraints are PostgreSQL-specific. Green CI on SQLite does not prove T1–T3 |

Add at least: deactivated user cannot hit `/api/v1/staff` with a still-valid access token (fails today); concurrent booking test against PostgreSQL; overpayment rejected; invoice list does not N+1 (query count).

---

## 14. Recommended fix order

1. **P0 — Double-booking.** Persist a range and add `EXCLUDE USING gist` (or `pg_advisory_xact_lock` on `staff_id` + date as a temporary lock). Keep the application overlap check.
2. **P1 — Authz source of truth.** Point `require_permissions` / `require_roles` at `app.auth.dependencies.get_current_user`. Consider a short-lived access token (5–10 min) or an allowlist/jti table if logout must kill access immediately.
3. **P1 — Money serialization.** `SELECT … FOR UPDATE` the invoice (or appointment) before inserting a SUCCESS payment; reject `new_paid > invoice.total`; map `IntegrityError` on invoice/commission unique indexes to 409; increment visit stats in SQL.
4. **P1 — Billing list N+1.** One query for page + paid totals + invoice ids.
5. **P1 — Login throttle** and disable `/docs` (or protect it) in production.
6. **P2 — Receptionist `STAFF_READ` (read-only roster)**, password policy, CORS/production guards, refund story, UTC vs salon timezone, staff nested-customer permission.
7. **P3 — Deduplicate** money/dates/staff-scope helpers; refresh README and architecture tree.

---

## 15. Module checklist

| Module | Layered | RBAC on router | Tests | Notes |
|---|---|---|---|---|
| Auth | Yes | Public login/refresh; `/me` uses DB user | Yes | Logout ≠ access revoke |
| Staff | Yes | Admin CRUD | Yes | Commission gate is `is_admin` |
| Services | Yes | Read: desk+staff; write/delete: admin | Yes | |
| Customers | Yes | Desk only | Yes | No delete route (soft-delete unused at API) |
| Schedules / availability | Yes | Desk+admin | Yes | No holiday table |
| Appointments | Yes | Desk full; staff own | Yes | Overlap race P0 |
| Billing | Yes | Desk+admin | Yes | List N+1; overpay; no refunds |
| Commissions | Yes | Admin all; staff own | Yes | Generated on paid-in-full |
| Tips | Yes | Desk write; staff own read | Yes | |
| Tasks | Yes | Admin assign; staff own | Yes | |
| Dashboard | Yes | Admin (`DASHBOARD_READ`) | Yes | SQL aggregates |
| Performance | Yes | Admin team; staff own card | Yes | SQL aggregates |
| Users | Models only | — | Via auth/staff | Docs say full module |
| Health | Router only | Public | Yes | No DB check |

---

## 16. Bottom line

Build quality is high for a V1: consistent layers, envelopes, pagination, snapshots, and SQL KPIs. Do not confuse that with production safety. **Booking integrity and token/session revocation are the two gates.** Until overlap is enforced in the database (or a transaction lock) and every request re-validates the live user, this backend should stay in staging.