# Фаза 2 — API (FastAPI) + Web (Next.js) — Детальный план

Цель
- Поднять минимально работоспособный слой API (FastAPI) и базовый веб‑интерфейс (Next.js + TS) для управления сущностями: Life Areas, Dreams, Goals, Projects, Habits, Tasks, Attachments (заглушка). Обеспечить генерацию TS‑клиента из OpenAPI, удобный локальный запуск и базовый CI.

Общие принципы
- Чистая архитектура: роуты (HTTP) тонкие → сервисный слой (CRUD/валидация) → ORM.
- Контракты вперёд: OpenAPI — единый источник правды для клиента.
- Минимизируем склейку: сгенерированный клиент, React Query, строгие DTO (Pydantic) отдельно от ORM.
- Эволюция без поломок: версионирование API `/v1/*`, заглушки там, где нужна доработка (подпись вложений, аутентификация).

Скоуп (MVP фазы 2)
- API (FastAPI):
  - `/health`
  - `/v1/life-areas` — CRUD, привязки опционально (без жёстких связей)
  - `/v1/dreams` — CRUD (+ список привязанных life areas)
  - `/v1/goals` — CRUD (+ опционально: `dream_id`, `project_id`)
  - `/v1/projects` — CRUD
  - `/v1/habits` — CRUD; `/v1/habits/{id}/logs` — create/list
  - `/v1/tasks` — CRUD (standalone или c `goal_id`/`project_id`/`habit_id`), смена статуса
  - `/v1/attachments` — заглушка генерации pre‑signed URL (вернём структуру для будущей подписи)
  - Пагинация (`limit`, `offset`), фильтры по `user_id`, статусам, датам (минимально).
  - Схемы Pydantic: Request/Response DTO; унифицированный формат ошибок.
  - Заглушка аутентификации: `current_user` → фиксированный `user_id` из ENV для локалки.
- OpenAPI → TS‑клиент:
  - Экспорт openapi.json (эндпойнт и/или скрипт) и генерация клиента в `packages/shared/client` (openapi-typescript).
  - Скрипт проверки «клиент синхронизирован» (generate → git diff пуст).
- Web (Next.js + TS):
  - App Router, базовый layout, React Query провайдер, .env.local.
  - Страницы CRUD: `/app/life-areas`, `/app/dreams`, `/app/goals`, `/app/projects`, `/app/habits`, `/app/tasks`, `/app/health`.
  - Формы создания/редактирования, таблицы/списки, уведомления об ошибках.
  - Используем только сгенерированный TS‑клиент.
- Makefile и DX:
  - `make api-dev`, `make web-dev`, `make api-openapi`, `make client-gen`.
  - Короткий README по запуску фазы 2.
- CI (минимум):
  - API: проверка импорта/сборки схем, OpenAPI экспорт.
  - Web: `npm ci`, `eslint`, `next build`.
  - Проверка синхронизации TS‑клиента.

Доставки (Deliverables)
- Папки:
  - `apps/api/app/api` (FastAPI) — main, deps, errors, settings, routers/*, schemas/*, services/*.
  - `packages/shared/client` — сгенерированный TS‑клиент + индекс.
  - `apps/web` — Next.js приложение (App Router) + страницы.
- Скрипты:
  - `scripts/export_openapi.sh` (или Make‑цель) — получить openapi.json.
  - `scripts/gen_client.sh` — генерация TS‑клиента.
- CI: `.github/workflows/api-web-ci.yml` — сборка и проверки.
- Документация: `PHASE2_PLAN.md`, `apps/web/README.md`, краткий раздел в корневом README.

API — детально
- Архитектура
  - `settings.py` (Pydantic Settings): `SELFOS_DATABASE_URL`, `SELFOS_ALLOW_ORIGINS`, `SELFOS_FAKE_USER_ID`.
  - `deps.py`: сессии БД, `current_user` (заглушка), пагинация.
  - `errors.py`: HTTPException фабрики, обработчики валидации.
  - `schemas/*`: DTO для всех сущностей (Create/Update/Out), пагинация `Page[T]`.
  - `services/*`: CRUD‑методы над ORM, маппинг DTO↔ORM, инварианты.
  - `routers/*`: эндпойнты, только сборка зависимостей и вызов сервисов.
  - `main.py`: FastAPI(app), CORS, роутеры, /health, OpenAPI конфиг.
- Контракты (примеры)
  - GET `/v1/life-areas?limit=20&offset=0` → `{ total, items: LifeAreaOut[] }`
  - POST `/v1/goals` body: `GoalCreate{ title, dream_id?, project_id?, life_area_ids?[] }` → `GoalOut`
  - PATCH `/v1/tasks/{id}` body: `TaskUpdate{ title?, status?, due_at? ... }` → `TaskOut`
- Правила
  - Пагинация limit<=100 по умолчанию 20; в ответе total по возможности или `next_cursor` (в MVP — total/offset).
  - Ошибки: `{ code, message, details? }` с HTTP статусами.

OpenAPI → TS‑клиент
- Экспорт: эндпойнт `/openapi.json` или `scripts/export_openapi.sh` (`curl` → файл).
- Генерация: `openapi-typescript openapi.json -о packages/shared/client/index.ts`.
- Post‑step: ESLint fix/Prettier; проверка чистоты git diff в CI.

Web (Next.js + TS)
- Структура:
  - App Router (`app/`), провайдеры (React Query), обёртка клиента (`ApiProvider`), базовые компоненты.
  - Страницы CRUD: списки (таблицы), формы, модалки удаления.
  - Хуки: `useLifeAreas()`, `useCreateGoal()`, и т.п. на базе сгенерированного клиента.
  - Обработка ошибок: тосты/уведомления, маппинг кодов API.
- ENV: `NEXT_PUBLIC_API_BASE_URL` для клиента.

Makefile цели
- `make api-dev` — запуск Uvicorn (`apps/api`).
- `make api-openapi` — экспорта openapi.json.
- `make client-gen` — генерация TS‑клиента (зависит от api-openapi).
- `make web-dev` — запуск Next.js dev.

CI (api-web-ci)
- Python job:
  - setup python + cache pip; установка deps (`apps/api/requirements.txt`)
  - import‑check (импорт app.api.main, запуск `python -m pip check`)
  - экспорт OpenAPI (curl) как артефакт
- Web job:
  - setup node + cache npm; `npm ci`; `npm run lint`; `npm run build`
  - генерация клиента: сверка, что `git diff` пуст после `make client-gen` (или FAIL)
- Политика: ветки `dev/phase2`, PR в `main` — обязательные проверки обоих джобов.

Пошаговый план (задачи)
1) API каркас
   - `main.py`, `settings.py`, `deps.py`, `errors.py`; CORS; `/health`.
   - Роутеры и схемы: life‑areas → dreams → goals → projects → habits (+logs) → tasks → attachments (stub).
   - Сервисный слой CRUD; пагинация/фильтры; unit‑smoke (минимум) опционально.
2) OpenAPI и клиент
   - Цель экспорта и генератор клиента; Make‑цели; документировать путь.
3) Web каркас
   - Next.js, React Query, базовый layout, интеграция клиента; страницы для сущностей.
4) Makefile и README
   - Цели запуска/генерации; краткая документация для локалки.
5) CI
   - Добавить `api-web-ci.yml` (2 джоба), кэш pip/npm, проверка клиента.
6) Полировка
   - Обработка ошибок, UX‑мелочи, пагинация UI.

Критерии приёмки
- API отвечает `/health`, CRUD‑эндпойнты по основным сущностям работают (200/201/204/404/422).
- Next.js страницы отображают списки и позволяют создавать/редактировать/удалять записи.
- TS‑клиент генерируется из OpenAPI и используется во фронте.
- CI `api-web-ci` зелёный (API джоб + Web джоб).

Риски и смягчение
- Дрифт контракта API ↔ клиент: обязательная проверка «generate → git diff пуст» в CI.
- Заглушка аутентификации: ограничиваем CORS; Phase 3 — OAuth/Passkeys.
- Индексы/производительность: сложные фильтры/поиск — в Phase 3 (сейчас только базовые фильтры/пагинация).
- Вложения: pre‑signed URL stub — реальная подпись/хранение в Phase 3.

Вне скоупа (фаза 2)
- MCP Gateway, внешние агенты, голос, фоновые воркеры Pub/Sub.
- Реальная аутентификация, публикации в соцсети, прод‑деплой Cloud Run.

Оценка сроков
- 1–1.5 недели на MVP при текущем объёме: API (3–4 дня), генерация клиента (0.5 дня), web (3–4 дня), CI+полировка (1–2 дня).
