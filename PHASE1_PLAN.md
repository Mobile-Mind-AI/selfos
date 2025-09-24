# Phase 1 — Database & Domain (Detailed Plan)

Objective
- Establish the core data model and migrations on Postgres (Cloud SQL-ready) with pgvector. Provide domain-layer foundations for Life Areas, Dreams, Goals, Habits, Projects, Tasks, Knowledge Graph, Outbox, Audit, and Memories.

Scope (Phase 1)
- Postgres schemas: `core`, `graph`, `memory`, `chat`, `agent`, `audit`, `outbox`.
- Tables: life_areas, life_area_links, dreams, goals, projects, habits, habit_logs, tasks, attachments; graph nodes/edges; memory.memories (pgvector); chat.{conversations,messages}; agent.{agents,runs}; audit.events; outbox.events.
- IDs: ULID strings across all tables.
- Indices: btree on foreign keys and status; GIN on JSONB where applicable; IVFFLAT index on vector embeddings.
- Alembic migrations: initial revision creates schemas and tables (+ pgvector extension), downgrade path included.
- Domain layer: SQLAlchemy models with schemas and naming conventions.
- Seed data: optional default Life Areas.

Out of scope (Phase 1)
- API endpoints, worker consumers, MCP gateway. (Begin in Phase 2+)
- Event publisher/dispatcher (create outbox schema only).
- Business logic beyond minimal repository scaffolding.

Deliverables
- Alembic-configured Python project (`apps/api`) containing:
  - SQLAlchemy models for core, graph, memory, chat, agent, audit, outbox.
  - Alembic env + initial migration `0001_initial.py` (creates schemas/tables, vector extension, indexes).
  - Config for DATABASE_URL via env.
- Docs: migrations usage notes (alembic upgrade/downgrade), Cloud SQL pgvector enable note.

Data Model (overview)
- LifeArea: id, user_id, name, color, created_at (unique per user: name)
- LifeAreaLink: life_area_id, user_id, object_type (dream|goal|project|task|habit), object_id
- Dream: id, user_id, title, description, status (ideation/incubating/active/archived), horizon (short/medium/long)
- Goal: id, user_id, dream_id?, project_id?, title, description, target_date?, status
- Project: id, user_id, title, description?, status
- Habit: id, user_id, title, schedule_rrule?, cadence_target?, period(day|week|month)?, streak, last_done_at?
- HabitLog: habit_id, occurred_at, value?, note?
- Task: id, user_id, goal_id?, project_id?, habit_id?, title, description?, status, due_at?, rrule?, effort_minutes?
- Attachment: id, user_id, ref_type, ref_id, gcs_path, mime, size_bytes?, created_at
- Graph: nodes(id, type, label, aliases JSONB); edges(src_type, src_id, rel, dst_type, dst_id, weight?, props JSONB)
- Memory: memories(id, user_id, text, embedding vector(dim), metadata JSONB, created_at)
- Chat: conversations(id, user_id, title?), messages(id, conversation_id, user_id, role, content, extracted JSONB, created_at)
- Agent: agents(id, user_id, name, type, scopes JSONB), runs(id, agent_id, user_id, input JSONB, output JSONB, status, costs JSONB, created_at)
- Audit: events(id, user_id, action, ref_type, ref_id, meta JSONB, created_at)
- Outbox: events(id, event_type, aggregate_type, aggregate_id, payload JSONB, status, attempts, next_attempt_at, created_at)

Indexes (key)
- core.tasks(user_id, status), core.tasks(user_id, due_at)
- core.goals(user_id, created_at desc)
- core.life_areas(user_id, name unique)
- memory.memories(user_id, created_at desc), memory.memories using ivfflat(embedding vector_cosine_ops)
- graph.edges(src_type, src_id), graph.edges(dst_type, dst_id)

Acceptance Criteria
- `alembic upgrade head` creates all schemas and tables without errors.
- `CREATE EXTENSION vector` executed (pgvector available).
- Downgrade drops tables safely.
- SQLAlchemy models map 1:1 to tables and pass basic metadata reflection.

Tasks & Sequence
1) Project skeleton for `apps/api` (requirements, settings, db engine, Base metadata).
2) Models: core (life areas, dreams, goals, projects, habits, habit_logs, tasks, attachments).
3) Models: memory (memories), graph (nodes/edges), chat (conversations/messages), agent (agents/runs), audit (events), outbox (events).
4) Alembic setup: `alembic.ini`, `env.py` pulling `Base.metadata`.
5) Initial migration: create schemas, create extension, create tables + indexes.
6) Optional seed: default life areas for a new user (script placeholder).
7) Docs: migration commands and Cloud SQL notes.

Cloud SQL Notes
- Ensure pgvector is enabled: `CREATE EXTENSION IF NOT EXISTS vector;` (requires Cloud SQL 14+).
- Use Serverless VPC connector for Cloud Run to reach Cloud SQL; app reads `DATABASE_URL`.

Risks/Mitigations
- pgvector dimension mismatch → fix by pinning a default dimension (e.g., 1536) and abstracting embedder.
- Cross-schema FKs → we specify schema-qualified FKs (e.g., `ForeignKey('core.users.id')`).
- Polymorphic links (LifeAreaLink) → no FKs for object_id; enforce via application/service layer.

---

This document is the source of truth for Phase 1 execution.
