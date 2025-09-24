# SelfOS Next — High-Level Implementation Plan (v0.1)

Goals
- Deliver a cost-efficient, serverless MVP with conversational capture, Life Coach agent, core work management, and weekly storytelling.
- Keep boundaries clean for future growth while minimizing moving parts now.

Guiding Constraints
- Backend: Python (FastAPI).  
- Data: Cloud SQL Postgres (+pgvector), GCS.  
- Events: Pub/Sub.  
- UI: Next.js + TypeScript.  
- Deploy: Cloud Run; autoscale-to-zero where possible.

---

## Phase 0 — Foundations (Week 1)
- Repo scaffolding: `apps/api`, `apps/mcp-gateway`, `apps/worker`, `apps/web`, `packages/shared`, `infra`.
- Common tooling: formatting (ruff/black), mypy, pytest, pre-commit, commit hooks.
- Base Dockerfiles + devcontainer; Taskfile/Makefile for common commands.
- IaC (Terraform skeleton): Cloud Run services, Cloud SQL (pgvector), Pub/Sub topics, GCS buckets, Secret Manager, Scheduler, VPC connector.
- CI/CD (GitHub Actions): build → lint/test → publish → deploy (staging).

Acceptance
- `make up` starts local stack; `terraform plan` valid; CI green on scaffold.

---

## Phase 1 — Database & Domain (Weeks 2–3)
- Define schemas (core, graph, memory, chat, agent, audit) with migrations (alembic).
- Core includes: life_areas, life_area_links (polymorphic), dreams, goals, projects, habits (+habit_logs), tasks (linkable to goal/project/habit or standalone), attachments.
- Implement repositories and domain services (hexagonal ports/adapters).
- Implement Outbox pattern and publisher to Pub/Sub.
- Seed data + fixtures; unit tests on domain logic.

Acceptance
- Migrations apply cleanly; CRUD services for users/life_areas/dreams/goals/projects/habits/tasks/entities pass tests.
- Outbox writes on mutations; publisher moves events to Pub/Sub (local emulator).

---

## Phase 2 — API & Web Skeleton (Weeks 3–4)
- FastAPI routes: auth, projects/goals/tasks CRUD, entities (graph), attachments (signed URLs).
- OpenAPI client generation; basic WebSocket/SSE channel for live updates.
- Next.js app: auth shell, navigation, tables for goals/tasks, simple entity browser.

Acceptance
- Web can create/edit tasks/goals, upload attachment, and see live updates.

---

## Phase 3 — Conversational Ingest (Weeks 4–5)
- Chat routes: post message → classify (LLM; intents include dream/goal/habit/project/task/note) → extract entities (incl. life areas) → draft actions.
- Prompt templates (versioned) + golden tests for classification/extraction.
- UI Inbox to review proposals and approve → commit via Idempotency-Key.

Acceptance
- From a chat like “I want to learn piano”, system proposes a Dream or Goal (depending on specificity) and starter tasks; user approves; items appear and are linked to a Life Area. From “I want to run 3x/week”, system creates a Habit with cadence and first check-ins.

---

## Phase 4 — Worker & Life Coach Agent (Weeks 5–6)
- Cloud Run Worker subscribed to Pub/Sub topics.
- Implement Life Coach agent loop: context → plan → policy → command → run logs.
- Daily planning via Cloud Scheduler → Pub/Sub `schedule.tick`.
- Embedding pipeline (pgvector) for selected content; memory search utility.
- Unified tooling:
  - Define Pydantic Tool Contracts (inputs/outputs) for core tools (tasks/goals/entities/memory/story).
  - Implement Tool Registry and Local Adapter (binds contracts to domain services with policy + audit hooks).

Acceptance
- Agent creates daily tasks or nudges on schedule; identifies neglected Life Areas, proposes balance actions; idempotency verified; runs logged.

---

## Phase 5 — Storytelling & Markdown Export (Week 7)
- Story generator: weekly summary for user or entity; Markdown output.
- UI page for stories; download/export.

Acceptance
- Weekly story renders with milestones and attachments; Markdown export works.

---

## Phase 6 — MCP Gateway (Week 8)
- Build separate MCP Gateway (Cloud Run) exposing tools: list/create tasks/goals, search/record memory, generate_story.
- Implement MCP→API service-to-service auth (IAM identity tokens, audience checks) and per-agent scopes/quotas.
- Full audit of tool calls to `agent.runs` and `audit.events`.
- Generate MCP tool JSON schemas from the same Pydantic Tool Contracts; use HTTP Adapter to call API Tool endpoints.

Acceptance
- External agent (test client) connects to MCP WS/SSE, lists tasks, creates one within scope via MCP→API, and audit shows tool calls.

---

## Phase 7 — Voice (Week 9)
- STT (Cloud Speech-to-Text) gateway; mic capture in web; streaming to API.
- TTS (Cloud TTS) for responses; playback in web.

Acceptance
- Speak a short goal; proposal appears; accept it; hear confirmation.

---

## Phase 8 — Social Integrations (Weeks 10–11)
- OAuth + token storage for Facebook/Instagram (Graph APIs).  
- Compose post from story (image + caption); user-initiated publish.

Acceptance
- User connects IG/FB; publishes a story segment to IG as a post/reel (as permitted).

---

## Phase 9 — Security & Observability Hardening (Parallel/Week 11)
- Rate limits, request validation, CORS review, secrets wiring.
- Structured logs, OTEL traces, metrics, budget alerts; DLQ handling.

Acceptance
- Error budgets/alerts configured; DLQ replay tooling; pen-test checklist passes.

---

## Phase 10 — Production Rollout (Week 12)
- Staging → prod promotion; backup/PITR for Cloud SQL; runbooks & SLOs.
- Cost dashboards and auto-scaling guardrails.

Acceptance
- Blue/green or canary deploy works; rollback verified; costs within target envelope.

---

## Deliverables Summary
- Source: `apps/api`, `apps/worker`, `apps/web`, `packages/shared`, `infra/terraform`.
- Docs: architecture, ops runbooks, API reference, prompt specs, MCP tools.
- CI/CD: automated tests, migrations, deploy to staging/prod.

---

## Risks & Mitigations
- LLM variability: golden tests, constrained schemas, fallback providers.
- Cost spikes: budgets, per-user caps, model selection strategy, caching.
- Cloud SQL limits: start small, add indexes carefully, use read-friendly queries; consider read replicas if needed.
- Pub/Sub ordering: design idempotent consumers; use keys to confine ordering when required.
- Social API constraints: require Business/Creator accounts; keep posting user-initiated.

---

## Out of Scope (MVP)
- Multi-tenant teams, RBAC beyond user-only.
- Advanced analytics BI; complex graph algorithms beyond adjacency queries.
- Full marketplace for third-party agents (future).

---

## Notes on Team & Timeline
- Solo/Small team: 10–12 weeks to MVP per phases above.
- Parallelization: Web and API can progress in parallel after Phase 1.
- Milestone demos every 1–2 weeks; tighten feedback loops.
