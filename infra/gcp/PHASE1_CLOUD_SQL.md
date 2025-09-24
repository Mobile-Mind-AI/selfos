# Phase 1 — Cloud SQL Deployment (GCP)

This guide helps you bring up Postgres (with pgvector) on Cloud SQL and apply Alembic migrations from `apps/api`.

## Prerequisites
- Google Cloud project + billing enabled
- gcloud CLI installed and authenticated (`gcloud init`)
- cloud-sql-proxy installed (https://cloud.google.com/sql/docs/postgres/sql-proxy)
- Python 3.11+ and `pip`

## 1) Create Cloud SQL Postgres Instance
```bash
PROJECT_ID="your-project"
REGION="us-central1"
INSTANCE="selfos-dev"
DB_NAME="selfos_dev"
DB_USER="selfos"
DB_PASS="selfos"   # choose a secure password for non-demo

gcloud config set project "$PROJECT_ID"

gcloud sql instances create "$INSTANCE" \
  --database-version=POSTGRES_15 \
  --cpu=1 --memory=4GiB \
  --region="$REGION" \
  --storage-auto-increase

gcloud sql users create "$DB_USER" --instance="$INSTANCE" --password="$DB_PASS"

gcloud sql databases create "$DB_NAME" --instance="$INSTANCE"
```

## 2) Enable pgvector Extension
Use the proxy to connect as a superuser (usually `postgres`) and run `CREATE EXTENSION`.
```bash
CLOUDSQL_INSTANCE="${PROJECT_ID}:${REGION}:${INSTANCE}"
LOCAL_PORT=6543
cloud-sql-proxy --port "$LOCAL_PORT" "$CLOUDSQL_INSTANCE" &
PROXY_PID=$!
trap 'kill $PROXY_PID' EXIT

# Run as postgres (set PGPASSWORD if needed)
psql "host=127.0.0.1 port=$LOCAL_PORT dbname=$DB_NAME user=postgres" -v ON_ERROR_STOP=1 -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## 3) Apply Alembic Migrations
From repo root:
```bash
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL="postgresql+psycopg://${DB_USER}:${DB_PASS}@127.0.0.1:${LOCAL_PORT}/${DB_NAME}"
alembic -c alembic.ini upgrade head
```

Alternatively, use the helper script:
```bash
cd apps/api
CLOUDSQL_INSTANCE="$CLOUDSQL_INSTANCE" DB_NAME="$DB_NAME" DB_USER="$DB_USER" DB_PASSWORD="$DB_PASS" \
  DB_SUPERUSER="postgres" DB_SUPERPASS="<postgres_password_if_set>" \
  ./scripts/cloudsql_migrate.sh
```

## 4) Verify
```bash
psql "host=127.0.0.1 port=$LOCAL_PORT dbname=$DB_NAME user=$DB_USER" -c "\\dn"   # schemas
psql "host=127.0.0.1 port=$LOCAL_PORT dbname=$DB_NAME user=$DB_USER" -c "\\dt core.*"
```

## Notes
- For production, restrict access via private IP + Serverless VPC and per‑service accounts.
- Store credentials in Secret Manager; never hardcode in CI.
- Next phases will add Cloud Run services and CI/CD.

