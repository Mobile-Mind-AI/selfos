.PHONY: help api-venv api-install bootstrap-local db-up db-migrate db-down cloudsql-migrate seed-areas fmt clean

help:
	@echo "Targets:"
	@echo "  api-venv            Create Python venv under apps/api/.venv"
	@echo "  api-install         Install apps/api requirements into venv"
	@echo "  bootstrap-local     Start local Postgres (pgvector) and run migrations"
	@echo "  db-up               Start local Postgres (pgvector) in Docker"
	@echo "  db-migrate          Apply Alembic migrations (requires DATABASE_URL)"
	@echo "  db-down             Stop local Postgres container"
	@echo "  cloudsql-migrate    Apply migrations to Cloud SQL via proxy"
	@echo "  clean               Remove Python caches"

api-venv:
	python3 -m venv apps/api/.venv

api-install: api-venv
	. apps/api/.venv/bin/activate && pip install -U pip && pip install -r apps/api/requirements.txt

bootstrap-local:
	bash apps/api/scripts/bootstrap_local.sh

db-up:
	PG_IMAGE=pgvector/pgvector:pg15 PG_CONTAINER=selfos-pg PG_PORT=5432 \
		docker run -d --rm --name $$PG_CONTAINER -e POSTGRES_USER=selfos -e POSTGRES_PASSWORD=selfos -e POSTGRES_DB=selfos_dev -p $$PG_PORT:5432 $$PG_IMAGE

db-migrate:
	@if [ -z "$$DATABASE_URL" ]; then echo "Set DATABASE_URL" >&2; exit 1; fi
	cd apps/api && . .venv/bin/activate 2>/dev/null || true && alembic -c alembic.ini upgrade head

db-down:
	-docker stop selfos-pg

cloudsql-migrate:
	cd apps/api && ./scripts/cloudsql_migrate.sh

clean:
	rm -rf **/__pycache__ **/*.pyc .pytest_cache

