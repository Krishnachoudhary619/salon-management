# Backend Final Review

**Role.** Principal Backend Architect  
**Date.** 2026-08-25  
**Version.** 0.1.0  
**Scope.** Complete V1 backend (`backend/app/**`, tests, Docker, Alembic) against `Salon_Backend_Blueprint.md` and `Salon_Backend_Architecture.md`  
**Tests.** 185 passed (unit + integration)

---

## Production readiness verdict

**Staging: yes. Live salon with concurrent front-desk use: no.**

The product surface is complete (auth through team performance). The process is deployable: liveness/readiness, structured logs, CORS and host allowlists, rate limits, security headers, DB connect retries, graceful drain, Docker + Alembic on boot.

Three domain defects from `Backend_Audit_Report.md` are **still open** and will cause real incidents:

| Blocker | Risk |
|---|---|
| Appointment overlap is application-only | Two concurrent bookings of the same slot both commit |
| Access tokens are not re-checked against the database | Deactivated or demoted users keep access for up to 30 minutes; logout does not kill the access token |
| Payments are not serialized or capped | Overpayment, duplicate commission, and lost visit counters under concurrent pay |

Treat this release as **V1 feature-complete for staging and internal demos**. Do not put a busy salon on it until the blockers above are closed. Details are in [Known Limitations](#3-known-limitations).

---

## 1. Release notes

### What this release is

Salon Management System **backend V1.0 feature set** (semver `0.1.0`). FastAPI + PostgreSQL, JWT + RBAC, request-scoped transactions, standard `{success, message, data/errors}` envelope, `/api/v1` prefix.

### Modules shipped

| Module | Capability |
|---|---|
| Auth | Login, logout, refresh rotation with reuse detection, `/me`, bcrypt, hashed refresh tokens |
| Staff | CRUD, linked user account, commission %, soft-deactivate disables login |
| Services | Catalog with snapshots used later on bookings |
| Customers | CRM search, visit stats updated when an invoice is paid in full |
| Schedules | Weekly windows, replace week, availability slots |
| Appointments | Book, edit, workflow, cancel, reschedule, calendar; availability engine on write |
| Billing | Invoice on `COMPLETED`, CASH/CARD/UPI payments |
| Commissions | Snapshot once when SUCCESS payments cover the invoice; never recalculated |
| Tips | Discretionary, stored separately from commission |
| Tasks | Admin assign; staff own; PENDING → IN_PROGRESS → COMPLETED |
| Dashboard | SQL KPIs: today/month revenue, volume, ticket size, top staff |
| Performance | Team + own-staff cards: revenue, customers served, completed, tips, commission |
| Ops | `/health`, `/ready`, JSON logs, CORS, rate limits, security headers, startup retry, graceful shutdown |

### Roles

- **ADMIN** — full API including dashboard, team performance, staff, commission %
- **RECEPTIONIST** — customers, catalog read, schedules, appointments, payments, invoices, tips. No reports, no staff CRUD, no commissions
- **STAFF** — own appointments, own earnings, own tasks, own performance card, catalog read

### Operations in this build

- `GET /health` — liveness (no database)
- `GET /ready` — ready only if the process is not draining and `SELECT 1` succeeds
- Production refuses weak `JWT_SECRET`, `CORS_ORIGINS=*`, `ALLOWED_HOSTS=*`, and `DEBUG=true`
- Docs (`/docs`, `/redoc`, `/openapi.json`) are **off** when `APP_ENV=production`
- In-process rate limit: 120 req/min per IP; login/refresh 10/min
- Security headers (nosniff, DENY frame, CSP, no-store, HSTS in production)
- Uvicorn `--timeout-graceful-shutdown`; `/ready` fails first so orchestrators stop sending traffic
- Docker image runs `alembic upgrade head` then uvicorn as non-root `appuser`
- Seed refuses default admin/staff passwords when `APP_ENV=production`

### Not in this release

- Multi-branch runtime (nullable `branch_id` only)
- Inventory, memberships, payroll, notifications, customer mobile app
- Refunds as a first-class API (enum exists; no endpoint)
- Redis-backed rate limiting (in-memory per process)
- PostgreSQL exclusion constraint on appointment time ranges

### Compatibility

- Python 3.12, PostgreSQL 16 (Compose), SQLAlchemy 2.0 async, Alembic revisions `0001` + `0002`
- Breaking vs earlier “foundation only” docs: the API is a full V1 salon backend. Clients should use `/api/v1/*` and the standard envelope.

---

## 2. Deployment checklist

Use this as the go-live runbook. Check every box before pointing a real salon at the API.

### 2.1 Infrastructure

- [ ] PostgreSQL 16+ with backups (PITR or nightly dump + restore test)
- [ ] TLS terminator in front of the API (Caddy, nginx, ALB). Set `ENABLE_HSTS=true` only after HTTPS works
- [ ] Single hostname for the API (e.g. `api.salon.example`) listed in `ALLOWED_HOSTS`
- [ ] SPA origin listed in `CORS_ORIGINS` (scheme + host + port, no trailing slash)
- [ ] If behind a reverse proxy, set `TRUST_PROXY_HEADERS=true` **only** if the proxy strips client `X-Forwarded-For` and sets a trusted value
- [ ] Secrets in the environment or a secret manager — never commit `.env`

### 2.2 Required production environment

```env
APP_ENV=production
DEBUG=false
LOG_JSON=true
LOG_LEVEL=INFO

DB_HOST=...
DB_PORT=5432
DB_NAME=...
DB_USER=...
DB_PASSWORD=...          # unique; special characters are URL-encoded

JWT_SECRET=...           # ≥32 chars, not a placeholder
CORS_ORIGINS=https://app.example.com
ALLOWED_HOSTS=api.example.com
ENABLE_HSTS=true
TRUST_PROXY_HEADERS=true # only behind a trusted proxy

RATE_LIMIT_ENABLED=true
WAIT_FOR_DATABASE=true
READY_CHECK_DATABASE=true
GRACEFUL_SHUTDOWN_SECONDS=30

SEED_ADMIN_PASSWORD=...  # not AdminPass123!
SEED_STAFF_PASSWORD=...  # not StaffPass123!
```

Process will **refuse to start** if JWT/CORS/hosts/DEBUG rules fail.

### 2.3 Database

- [ ] `alembic upgrade head` (Compose/API entrypoint already does this)
- [ ] Confirm tables exist (`appointments`, `payments`, `commissions`, …)
- [ ] Run seed **once** with unique production passwords: `python -m app.database.seed` from `backend/`
- [ ] Change the seeded admin password after first login (no self-service reset exists)
- [ ] Do not point the app at SQLite

### 2.4 Process and probes

- [ ] Replicas: 1 until overlap locking exists (see limitations). Horizontal scale **increases** double-book risk
- [ ] Liveness: `GET /health` → 200
- [ ] Readiness: `GET /ready` → 200 and `data.checks.database.status = ok`
- [ ] SIGTERM: `/ready` becomes 503, then connections drain, then exit
- [ ] Docker healthcheck is liveness only (`/health`); Kubernetes should use `/ready` as readinessProbe
- [ ] `uvicorn` graceful timeout ≥ `GRACEFUL_SHUTDOWN_SECONDS`

Suggested Kubernetes:

```yaml
livenessProbe:
  httpGet: { path: /health, port: 8000 }
  periodSeconds: 30
readinessProbe:
  httpGet: { path: /ready, port: 8000 }
  periodSeconds: 5
terminationGracePeriodSeconds: 45
```

### 2.5 Smoke test (after deploy)

- [ ] `POST /api/v1/auth/login` as admin
- [ ] Create staff, weekly schedule, service, customer
- [ ] `GET /api/v1/availability` then `POST /api/v1/appointments`
- [ ] Walk status to `COMPLETED`, pay invoice, confirm commission row
- [ ] Add a tip; confirm dashboard and `/performance/staff/{id}`
- [ ] Receptionist token: 403 on `/dashboard/overview` and `/performance/team`
- [ ] Staff token: 200 on own performance, 403 on another staff id
- [ ] Unauthenticated `/api/v1/staff` → 401
- [ ] `/docs` → 404 in production

### 2.6 Do not go live until

- [ ] Appointment overlap enforced in PostgreSQL (or a transaction lock) — see limitation L1
- [ ] Protected routes load the user from the database (active + live roles) — L2
- [ ] SUCCESS payments cannot exceed invoice remaining; unique invoice/commission races mapped to 409 — L3

If those three are skipped, run **only** as a single-user staging demo.

---

## 3. Known limitations

Severity matches `Backend_Audit_Report.md`.

### Blockers for a live salon

**L1 — Double-booking (P0)**  
Availability reads busy intervals, then inserts. No `SELECT … FOR UPDATE`, no advisory lock, no `EXCLUDE USING gist` on a time range. Two concurrent `POST /appointments` for the same staff/slot can both succeed. The B-tree on `(staff_id, appointment_date, start_time, end_time)` does not prevent overlap.

**L2 — Access tokens outlive account changes (P1)**  
`require_permissions` uses JWT claims only (`app.common.dependencies.get_current_user`). `/auth/me` reloads the user; the rest of the API does not. Deactivate staff, change roles, or logout: the Bearer token works until `ACCESS_TOKEN_EXPIRE_MINUTES` (default 30). Logout revokes **refresh** tokens only.

**L3 — Money races and overpayment (P1)**  
- SUCCESS amount is not capped at remaining balance  
- Invoice/commission create is check-then-insert; unique partial indexes exist on PostgreSQL but `IntegrityError` is not mapped to 409  
- `customers.visit_count` / `total_spent` are read-modify-write in Python  
- `REFUNDED` is in the enum; there is no refund API; dashboard revenue does not subtract refunds  

### Product / RBAC

**L4 — Receptionist cannot list staff (P2)**  
`STAFF_READ` is admin-only. Front desk must already know `staff_id` UUIDs. Schedules return ids without names.

**L5 — Staff can create customers via booking (P2)**  
`AppointmentCreateRequest.customer` calls `get_or_create_by_phone` without `CUSTOMER_WRITE`. Staff can also pass any `customer_id` UUID.

**L6 — Weak passwords (P2)**  
Minimum length is 1 character (bcrypt 72-byte cap only). No complexity policy.

**L7 — Login enumeration (P2)**  
Unknown user: `"Invalid email or password"`. Disabled account: `"Account is disabled"`. Missing users skip `verify_password` (timing).

**L8 — No login lockout (P2)**  
Rate limits reduce brute force; they are per IP, in-memory, and reset on process restart. Multiple API replicas do not share a counter.

### Ops / correctness

**L9 — UTC vs salon local time (P2)**  
Dashboard and performance “today / this month” use `datetime.now(UTC).date()`. An evening IST visit can land on the next UTC day.

**L10 — Rate limit and drain state are per process (P2)**  
Sliding window and in-flight counts are not shared across replicas. Fine for one API container; wrong as a cluster-wide throttle.

**L11 — Billing list N+1 (P1)**  
Invoice and payment list endpoints run extra queries per row (up to `limit=100`).

**L12 — Tests are SQLite (P2)**  
CI does not exercise PostgreSQL partial unique indexes or exclusion constraints. Green pytest is necessary, not sufficient for L1/L3.

**L13 — No leave/holiday calendar (P2)**  
Availability is weekly `staff_schedules` only.

**L14 — Financial rows are soft-deletable (P1, schema)**  
Invoices, payments, commissions, and tips have `is_deleted`. Soft-deleting a SUCCESS payment rewrites history. No void/refund document flow.

**L15 — Docs and README drift (P3)**  
`backend/README.md` still says “foundation layer only.” Architecture tree omits `performance/` and treats `users/` as a full module.

---

## 4. Future improvements

Ordered by value for a real salon.

### Must-do before production traffic

1. **Exclusion constraint** (or `pg_advisory_xact_lock` on staff + date) for non-overlapping active appointments. Keep the application availability check.
2. **Point `require_permissions` at `app.auth.dependencies.get_current_user`** so every request sees `is_active` and live roles. Optionally shorten access TTL or track access `jti` if logout must be immediate.
3. **Serialize payments** (`SELECT invoice FOR UPDATE`), reject `new_paid > total`, map unique violations to 409, increment visit stats in SQL.
4. **PostgreSQL in CI** (or a staging soak) with concurrent booking and double-pay tests.

### Should-do in the next iteration

5. Receptionist read-only staff roster (`STAFF_READ` or a slim `/staff/directory`).
6. Password policy, dummy hash on unknown login, identical error for disabled accounts.
7. Redis (or equivalent) rate limit when running more than one API replica.
8. Salon timezone setting; KPI windows in local civil dates.
9. Refund/void as append-only rows; subtract from revenue metrics.
10. Fix billing list N+1 (join paid totals once).
11. Holiday/leave exceptions for availability.
12. Make financial tables append-only (drop `is_deleted` or ignore it in money queries).

### Later product

13. Multi-branch: enforce `branch_id` on queries once branches exist  
14. Inventory / product consumption on appointment  
15. Memberships and packages  
16. Payroll runs (commissions + tips are inputs, not payroll)  
17. Notification outbox (WhatsApp / SMS)  
18. Customer self-booking app  
19. Shared helpers: money rounding, date windows, `_scoped_staff_id`  
20. Coverage gate at 80% measured on PostgreSQL  

---

## Verification summary

| Area | Status |
|---|---|
| Blueprint modules 1–12 | Shipped |
| Layering, envelope, pagination, RBAC shape | Pass |
| `/health` + `/ready` | Pass |
| Structured logging + secret redaction | Pass |
| Production CORS / hosts / JWT / DEBUG guards | Pass |
| Rate limiting (single process) | Pass |
| Security headers | Pass |
| DB startup retry + pool recycle/pre-ping | Pass |
| Graceful shutdown drain | Pass |
| Docker non-root + Alembic on boot | Pass |
| Concurrent booking integrity | **Fail** |
| Token revocation / live user check | **Fail** |
| Concurrent payment integrity | **Fail** |
| Refunds / tax / timezone | Not in V1 |

**Recommendation.** Tag this as **staging V1**. Keep one API replica. Use it to build the frontend and train workflows. Close L1–L3, then repeat this review before the first paid salon day.
