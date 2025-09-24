# SelfOS — Legacy Architecture Summary (Pre-Refactor)

Version: snapshot before refactor  
Branch: `refactoring/architecture`  
Date: generated from repo docs and code

This document captures the essential architecture, components, and design decisions of the existing SelfOS system to preserve institutional knowledge during the reset. It consolidates the main docs and code structure so we can selectively port what’s valuable into the new architecture.

## 1) High-Level Overview

Mission: Personal “life OS” that turns goals, values, and dreams into actionable, trackable experiences.  
Approach: Multi-app monorepo with a typed FastAPI backend, AI orchestration service, Model Context Protocol (MCP) server, and a Flutter front-end. Persistence includes PostgreSQL, Redis, and Weaviate (vector store).

Textual architecture:

User ↔ Flutter (Web/Mobile/Desktop)
           ↓
      API Gateway (FastAPI)
           ↓
  ├── Backend API (CRUD, business logic)
  ├── MCP Server (AI agent protocol)
  ├── AI Engine (provider-agnostic orchestration)
  ├── Memory Engine (RAG/vector search)
  ├── Storytelling & Notifications
  └── Integrations (Calendar, Social)
           ↓
   Persistence: PostgreSQL, Redis, Weaviate
           ↓
       Eventing: Redis Streams (planned/partial)

Key strengths to retain:
- Clear separation of HTTP (routers) vs business logic (services) in backend.
- Provider-agnostic AI orchestration with failover and caching.
- MCP server enabling standardized AI access to platform data.
- Assistant personalization (assistant profiles, onboarding, preview endpoints).
- Solid documentation breadth and dev environment via Docker Compose.

## 2) Repository Structure (Monorepo)

- apps/backend_api: FastAPI app with routers/services/models/schemas, tests, migrations.
- apps/ai_engine: AIOrchestrator with OpenAI, Anthropic, and Mock provider clients.
- apps/mcp_server: MCP server for secure AI integrations (CLI/Web/FastAPI transports).
- apps/selfos: Flutter app (Riverpod state), auth flows present, core UI partial.
- libs/prompts: Centralized prompt templates for AI flows.
- libs/shared_models, libs/utils: Placeholders intended for cross-service models/utils.
- docs: Detailed architecture, API, and system docs.
- infra: Dockerfiles, k8s manifests (planned), CI/CD scaffolding.
- docker-compose.yml: Postgres, Redis, Weaviate, backend, MCP, optional frontend.

## 3) Backend API (FastAPI)

Tech: Python 3.11+, FastAPI, SQLAlchemy ORM, Pydantic.  
Structure: routers/ (HTTP), services/ (business), models/ (DB), schemas/ (validation).  
Auth: Firebase Admin + JWT.  
Caching/Events: Redis.  
Testing: Extensive suite (docs claim ~87% coverage), many unit/integration tests.

Representative endpoints:
- Auth: /auth/register, /auth/login, /auth/me
- Core: /api/goals, /api/tasks, /api/life_areas, /api/media, /api/preferences
- AI & Analytics: /api/ai/*, /api/conversation, /api/feedback, /api/stories
- Assistant personalization: /api/assistant_profiles (CRUD, onboarding, config, default, preview)
- Health: /health

Data highlights:
- Assistant profiles with personality style (formality, directness, humor, empathy, motivation), temperatures, model, language, default flags, public visibility, ownership/versioning.
- Core entities: users, goals, tasks, life_areas, media, memory_items, feedback/stories.
- Indexing for common queries (user+created, user+status, due date, memory timestamp).
- Archival plan for high-volume tables (e.g., stories, feedback).

Security:
- JWT auth, bcrypt hashing, Pydantic validation, CORS.  
- Gaps previously noted: rate limiting, input sanitization audit, security scanning, secrets management.

## 4) AI Engine (apps/ai_engine)

Purpose: Orchestrate multiple AI providers behind a single interface with fallback and caching.

Components:
- Provider clients: OpenAIClient, AnthropicClient, MockClient.
- Operations: goal decomposition, task generation, conversational chat, health checks.
- Configurable model settings per provider; response caching with TTL; metrics collection.

Rationale to keep:
- Clean provider abstraction enables incremental providers or on-prem LLMs.
- Fallback logic increases reliability and cost control.

## 5) MCP Server (apps/mcp_server)

Purpose: Model Context Protocol server exposing SelfOS capabilities to AI agents via standardized tools.  
Transports: stdio, WebSocket, SSE; FastAPI integration available.  
Security: Firebase/API-key hooks; auth required by default for sensitive tools.  
Coverage: Goals API complete; projects/tasks framework started; 30+ tests present.

Rationale to keep:
- MCP unlocks safe, structured AI access with principled permissions.

## 6) Frontend (Flutter)

State: Riverpod.  
Status: Auth/onboarding flows present; core dashboards (goals/tasks/progress) partial/missing.  
Target platforms: Android, iOS, Web, Desktop.

Decision for new arch:
- Either keep Flutter and focus on a smaller MVP surface, or reset with a web-first SPA for velocity. Trade-offs to be decided.

## 7) Memory & RAG

Vector store: Weaviate (dev container), with a memory service abstraction and RAG integration (search memories to provide context for AI).

Design points:
- Vector store access abstracted to enable Pinecone/Weaviate/local embeddings.
- Conversation enhancement pipeline pulls relevant memories.

## 8) Infrastructure & Ops

Local dev:
- docker-compose: Postgres, Redis, Weaviate, Backend, MCP, optional Frontend.
- Firebase service account mounted into containers for auth.

Production (planned):
- CDN for static, load balancer, backend cluster, DB cluster, Redis cluster, vector store; monitoring stack (Prometheus/Grafana/Jaeger) planned.

CI/CD:
- GitHub workflows present for dependency updates, deploy, monitoring, release, security scans (varying completeness).  
- Testing commands and coverage targets documented per app.

## 9) Performance & Monitoring (as-documented)

Targets/claims:
- API p95 < 1.5s; DB avg < 100ms; memory retrieval < 500ms.
- Scalability: 1k+ concurrent now, 10k+ target; 10M+ DB rows target; 100M+ embeddings.

Gaps:
- Centralized metrics/observability infra not fully implemented.  
- Load and security testing not systematized.

## 10) Known Gaps & Technical Debt

- Frontend MVP gaps: goals/tasks dashboards, progress visualization, polish.
- Security: rate limiting, sanitization audit, secret mgmt, automated scanning.
- Shared libraries: `libs/shared_models` and `libs/utils` are placeholders; duplication risk across services.
- Memory boundaries: clarify when to use vector search vs. relational/core DB flows.
- Production hardening: monitoring, CI/CD, backup/PITR, RBAC/audit, SSO.

## 11) Suggested “Keep/Port” Candidates

- Backend layering pattern (routers → services → models/schemas) and selected mature services: goals, tasks, assistant profiles, progress.
- AI orchestrator provider abstraction and caching/fallback logic.
- MCP server’s tool structure and security shims.
- Assistant personalization domain model and onboarding/preview flows.
- Core docs that remain accurate after pruning (to be curated).
- Dev docker-compose for rapid local iterations (reduced set).

## 12) What to Rethink

- Frontend scope and stack for MVP velocity (smaller surface, tighter feedback loops).
- Security posture (rate limiting, secrets, scans, input validation) as first-class.
- Observability and CI/CD from day one.
- Narrower MVP API surface with stricter versioning and contract tests.
- Simpler memory story: one vector store abstraction with clear ownership and data lifecycle.

## 13) Historical Runbook (abridged)

- Backend dev: `uvicorn main:app --reload` (or scripts), tests via `pytest` with coverage.
- DB management: Alembic migrations, `manage_db.py` for init/archive/analyze.
- MCP: CLI/stdio or FastAPI integration on 8001; `run_tests.py`.
- Local compose: bring up DB/Redis/Weaviate + backend/MCP; optional frontend profile.

## 14) Glossary

- MCP: Model Context Protocol enabling AI tools to call platform functions securely.
- RAG: Retrieval-Augmented Generation using vector search to enrich prompts with context.
- Assistant Profile: Per-user assistant configuration (style, language, model, defaults).

---

This summary preserves the intent and working patterns of the prior system without prescribing the new design. Use it to decide which capabilities and patterns should be ported, simplified, or replaced in the upcoming architecture.

