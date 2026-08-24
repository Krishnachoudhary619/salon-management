# Salon Backend

FastAPI backend for the Salon Management System. This package currently contains the **foundation layer** only. Business modules (auth, staff, appointments, billing, etc.) will be added incrementally.

## Tech stack

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0 (async)
- Alembic
- Pydantic v2
- JWT + RBAC

## Architecture

```text
Router → Service → Repository → Database
```

- Routers stay thin
- Business logic lives in services
- Repositories perform database operations only

## Local setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

Update `JWT_SECRET` in `.env` before any production deploy.

## Run the API

```bash
uvicorn app.main:app --reload
```

- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/health

## Tests

```bash
pytest
```

## API response format

Success:

```json
{
  "success": true,
  "message": "Operation successful",
  "data": {}
}
```

Error:

```json
{
  "success": false,
  "message": "Validation error",
  "errors": []
}
```
