.PHONY: help api-venv api-install bootstrap-local db-up db-migrate db-down cloudsql-migrate clean

SHELL := /bin/bash
.DEFAULT_GOAL := help

# Auto-generated help from targets annotated with `##` descriptions
help: ## Show all make targets (auto-generated)
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage: make <target>\n\nTargets:\n"} \
	/^[a-zA-Z0-9_\/.\-]+:.*##/ { printf "  %-24s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

api-venv: ## Create Python venv under apps/api/.venv
	python3 -m venv apps/api/.venv

api-install: api-venv ## Install apps/api requirements into venv
	. apps/api/.venv/bin/activate && pip install -U pip && pip install -r apps/api/requirements.txt

bootstrap-local: ## Start local Postgres (pgvector) and run migrations
	bash apps/api/scripts/bootstrap_local.sh

db-up: ## Start local Postgres (pgvector) in Docker
	PG_IMAGE=pgvector/pgvector:pg15 PG_CONTAINER=selfos-pg PG_PORT=5432 \
		docker run -d --rm --name $$PG_CONTAINER -e POSTGRES_USER=selfos -e POSTGRES_PASSWORD=selfos -e POSTGRES_DB=selfos_dev -p $$PG_PORT:5432 $$PG_IMAGE

db-migrate: ## Apply Alembic migrations (requires DATABASE_URL)
	@if [ -z "$$DATABASE_URL" ]; then echo "Set DATABASE_URL" >&2; exit 1; fi
	cd apps/api && . .venv/bin/activate 2>/dev/null || true && alembic -c alembic.ini upgrade head

db-down: ## Stop local Postgres container
	-docker stop selfos-pg

cloudsql-migrate: ## Apply migrations to Cloud SQL via proxy
	cd apps/api && ./scripts/cloudsql_migrate.sh

clean: ## Remove Python caches
	rm -rf **/__pycache__ **/*.pyc .pytest_cache
