# Free UAT deploy

Use this stack so the client can click a public URL. No credit card is required.

| Piece | Free host | What you get |
|---|---|---|
| Postgres | [Neon](https://console.neon.tech) | Managed database |
| FastAPI | [Render](https://dashboard.render.com) | `https://salon-api-xxxx.onrender.com` |
| Next.js | [Vercel](https://vercel.com) | `https://salon-management-xxxx.vercel.app` |

Free tiers sleep when idle. The first open after a quiet period can take **30–90 seconds**. Tell the client to wait, then refresh once.

Demo login after seed:

- Admin: `admin@example.com` / `AdminPass123!`
- Staff password (seeded stylists): `StaffPass123!`

Change those before a wider share. They are the same defaults as local development.

## 1. Neon database

1. Sign in at [console.neon.tech](https://console.neon.tech) with GitHub.
2. Create a project (Postgres 16, any region close to your client).
3. Open **Connection details**.
4. Copy the **direct** connection string (host without `-pooler`). It looks like:

   `postgresql://user:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require`

Use the direct URL, not the pooled one. Render keeps the API process alive, so a small persistent pool is enough.

## 2. Render API

The repo already has `render.yaml`.

1. Push the latest `main` to GitHub (this repo is already connected).
2. In Render: **New** → **Blueprint** → pick `salon-management`.
3. When asked for `DATABASE_URL`, paste the Neon string from step 1.
4. Create the `salon-api` web service on the **Free** plan.
5. Wait until the deploy is live, then open:

   `https://<your-service>.onrender.com/health`

   You should see a JSON health response. `/docs` stays available because this UAT uses `APP_ENV=staging`.

If you prefer the dashboard instead of a Blueprint:

- **Root directory:** `backend`
- **Runtime:** Python 3.12
- **Build:** `pip install -r requirements.txt`
- **Start:** `sh docker-entrypoint.sh`
- **Health check:** `/health`
- Env vars from `render.yaml` (`APP_ENV=staging`, `RUN_SEED=true`, `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS=*`)

Startup runs migrations and the idempotent seed.

## 3. Vercel frontend

1. Sign in at [vercel.com](https://vercel.com) with the same GitHub account.
2. **Add New** → **Project** → import `salon-management`.
3. Set **Root Directory** to `frontend`.
4. Framework: Next.js (auto-detected).
5. Add this environment variable:

   | Name | Value |
   |---|---|
   | `NEXT_PUBLIC_API_BASE_URL` | `https://<your-service>.onrender.com/api/v1` |

6. Deploy. Copy the Vercel URL.

After the first successful deploy, optionally tighten CORS on Render:

```text
CORS_ORIGINS=https://salon-management-xxxx.vercel.app
```

Then redeploy the API. `*` is fine for a short private UAT.

## 4. What to send the client

- Website / booking: `https://<vercel-app>.vercel.app`
- Admin: `https://<vercel-app>.vercel.app/dashboard`
- Login: `admin@example.com` / `AdminPass123!`

Warn them that the first visit after idle time can be slow while Render and Neon wake up.

## If something fails

- **Render build / boot error:** open the service logs. Most first-boot failures are a bad `DATABASE_URL` or Neon still waking. Confirm `/health` after a minute.
- **Frontend loads, login or booking fails:** `NEXT_PUBLIC_API_BASE_URL` must end with `/api/v1` and match the live Render URL. Rebuild the Vercel project after changing it.
- **Browser CORS error:** Render `CORS_ORIGINS` must include the exact Vercel origin, or stay `*` for UAT.
- **Empty catalog / cannot log in:** `RUN_SEED` must have been `true` on the first successful boot. You can set it and trigger a manual Render deploy; seed is safe to re-run.
