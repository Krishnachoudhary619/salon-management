# Salon Management System

Monorepo for the salon management product.

```text
salon-management/
├── backend/                 FastAPI API
├── frontend/                Web client
├── docker-compose.yml       Shared local stack
├── Salon_Backend_*.md       Backend source-of-truth docs
└── README.md
```

| Workspace | Stack | Status |
|---|---|---|
| `backend/` | FastAPI, PostgreSQL, SQLAlchemy 2.0, JWT, RBAC | Foundation complete |
| `frontend/` | Web client | Workspace ready |

Architecture source of truth:

- [Salon_Backend_Blueprint.md](./Salon_Backend_Blueprint.md)
- [Salon_Backend_Architecture.md](./Salon_Backend_Architecture.md)

## Backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload
```

- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/health

```bash
cd backend
pytest
```

## Frontend

The `frontend/` workspace is reserved for the web client. Scaffolding will land there when frontend work starts.

## Docker (from repo root)

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

The API container runs `alembic upgrade head` on startup.

## Free UAT (client review)

Neon (Postgres) + Render (API) + Vercel (web). Step-by-step: [DEPLOY.md](./DEPLOY.md).

## Pre-commit

```bash
cd backend
source .venv/bin/activate
pip install pre-commit
cd ..
pre-commit install
```
