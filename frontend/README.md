# Salon Frontend

Next.js 15 web client for the Salon Management System.

## Stack

- Next.js 15 (App Router)
- TypeScript
- Tailwind CSS + ShadCN UI primitives
- TanStack React Query
- Axios
- React Hook Form + Zod
- Sonner (toasts)

## Getting started

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

The app runs at [http://localhost:3000](http://localhost:3000) and expects the backend at `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000/api/v1`).

## Environment

| Variable | Description |
| --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | Backend API base URL including `/api/v1` |
| `NEXT_PUBLIC_APP_NAME` | App title shown in the browser |
| `NEXT_PUBLIC_ENABLE_QUERY_DEVTOOLS` | Set to `true` to show React Query devtools |

## Folder structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router (layout, globals)
│   ├── components/
│   │   ├── auth/               # AuthProvider, RouteGuard, RoleGate, PermissionGate
│   │   ├── feedback/           # Loading and error UI
│   │   ├── providers/          # AppProviders (Query + Auth + Toaster)
│   │   └── ui/                 # ShadCN-style primitives
│   ├── config/                 # env, query client, routes
│   ├── hooks/                  # useAuth, usePermissions, useApiError
│   ├── lib/
│   │   ├── api/                # Axios client, errors, auth API
│   │   ├── auth/               # Token storage, RBAC helpers
│   │   └── schemas/            # Zod schemas (e.g. login)
│   └── types/                  # Shared TypeScript types
├── .env.example
└── components.json             # ShadCN config
```

## Foundation modules

### API client (`src/lib/api/`)

- Axios instance with bearer token injection
- Automatic refresh on 401 via `/auth/refresh-token`
- `apiRequest` / `apiRequestOptional` unwrap the backend `{ success, message, data }` envelope
- `ApiError` normalizes HTTP and validation errors

### React Query (`src/config/query-client.ts`)

- Shared `QueryClient` factory for server and browser
- Default retry skips 401 responses
- `queryKeys.auth.me` for the current user session

### Authentication (`src/components/auth/`)

- `AuthProvider` bootstraps session from stored tokens and loads `/auth/me`
- `registerUnauthorizedHandler` clears session and redirects to `/login` on expiry
- `useAuth()` exposes `user`, `login`, `logout`, `isBootstrapping`

### Role and permission guards

- `RouteGuard` — redirect unauthenticated users; optional role/permission checks
- `RoleGate` / `PermissionGate` — inline conditional rendering
- `usePermissions()` — `can`, `canAny`, `hasRole`, `isAdmin` helpers mirroring backend RBAC

### Feedback

- `toast` wrapper around Sonner with `fromError` helper
- `LoadingSpinner`, `PageLoader`, `FullPageLoader`, `LoadingState`
- `ErrorDisplay` with optional retry action

## Scripts

| Command | Description |
| --- | --- |
| `npm run dev` | Start dev server (Turbopack) |
| `npm run build` | Production build |
| `npm run start` | Serve production build |
| `npm run lint` | ESLint |
| `npm run typecheck` | TypeScript check |

## Notes

- Feature screens are not built yet; only the foundation is in place.
- Route protection is client-side because tokens are stored in `localStorage`.
- Login schema lives at `src/lib/schemas/auth.ts` for the upcoming login screen.
