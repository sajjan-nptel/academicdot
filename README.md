# AcademicDot — Tenants API

A **FastAPI** service that provides CRUD endpoints for the `tenants` PostgreSQL table used in AcademicDot's multi-tenant platform.

---

## Project Structure

```
academicdot/
├── main.py          # FastAPI application & routes
├── models.py        # SQLAlchemy ORM model
├── schemas.py       # Pydantic request/response schemas
├── database.py      # Async engine, session factory & DI helper
├── config.py        # Pydantic-Settings configuration
├── encryption.py    # Fernet encryption/decryption helpers
├── requirements.txt # Python dependencies
├── .env.example     # Environment variable template
└── README.md        # This file
```

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python      | ≥ 3.11  |
| PostgreSQL  | ≥ 14    |

---

## Quick Start

### 1. Clone & create a virtual environment

```bash
git clone https://github.com/sajjan-nptel/academicdot.git
cd academicdot
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_NAME` | Database name | `academicdot` |
| `DB_USER` | Database user | `postgres` |
| `DB_PASSWORD` | Database password | *(required)* |
| `DB_POOL_SIZE` | Connection pool size | `10` |
| `DB_MAX_OVERFLOW` | Extra connections beyond pool | `20` |
| `DB_POOL_TIMEOUT` | Pool checkout timeout (s) | `30` |
| `DB_SSL_ENABLED` | Require SSL for DB connections | `false` |
| `ENCRYPTION_KEY` | Fernet key for encrypted fields | *(required)* |
| `APP_ENV` | `development` / `production` | `development` |
| `APP_HOST` | Bind host | `0.0.0.0` |
| `APP_PORT` | Bind port | `8000` |
| `DEBUG` | Enable SQLAlchemy echo | `false` |
| `CORS_ORIGINS` | Comma-separated allowed origins | `*` |

#### Generate an encryption key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Paste the output into `ENCRYPTION_KEY` in your `.env`.

### 4. Apply the database schema

```bash
psql -U postgres -d academicdot -f postgrey.sql
```

### 5. Run the server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive docs are available at:
- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

---

## API Endpoints

### Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check |

### Tenants

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/tenants/` | List tenants (paginated) |
| `GET` | `/tenants/search?q=<term>` | Search by name, email, or slug |
| `GET` | `/tenants/by-subdomain/{subdomain}` | Fetch by subdomain |
| `GET` | `/tenants/by-slug/{node_slug}` | Fetch by slug |
| `GET` | `/tenants/{tenant_id}` | Fetch by `node_id` |
| `POST` | `/tenants/` | Create a new tenant |
| `PUT` | `/tenants/{tenant_id}` | Update tenant fields |
| `DELETE` | `/tenants/{tenant_id}` | Soft-delete tenant |

### Pagination query parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `page` | `1` | Page number (1-based) |
| `page_size` | `20` | Items per page (max 100) |

### List tenants extra parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `active_only` | `true` | Filter to active, non-suspended tenants |

---

## Security Notes

- `db_password`, `db_user`, and `api_endpoint_key` are **always encrypted** (Fernet) before being stored. Plain-text values are never persisted.
- Encrypted values are **never returned** in API responses. The `has_api_key` boolean indicates whether an API key exists.
- Use strong, unique `ENCRYPTION_KEY` values and rotate them via a proper key-management process in production.
- Set `CORS_ORIGINS` to explicit domains in production instead of `*`.

---

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad request / validation error |
| 404 | Tenant not found |
| 409 | Duplicate subdomain or slug |
| 500 | Internal server / encryption error |