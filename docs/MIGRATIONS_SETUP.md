<!-- docs/MIGRATIONS_SETUP.md -->
# Database Migrations Setup

This guide explains how to manage database schema migrations for the backend API using Alembic.

## Prerequisites
- `DATABASE_URL` environment variable set to your Postgres instance (e.g., from `docker-compose`)
- Dependencies installed:
  ```bash
  cd apps/backend_api
  pip install -r requirements.txt
  ```

## Directory Structure
```text
apps/backend-api/
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
├── db.py
├── models.py
└── main.py
```

## Create Initial Migration
```bash
cd apps/backend_api
# Autogenerate a new revision based on models
alembic revision --autogenerate -m "initial schema"
```

## Apply Migrations
```bash
cd apps/backend_api
alembic upgrade head
```

After running `upgrade`, your Postgres database will have the tables:
- users
- goals
- tasks
- memory_items

_You can add further revisions with `alembic revision -m "<message>"` and upgrade as needed._