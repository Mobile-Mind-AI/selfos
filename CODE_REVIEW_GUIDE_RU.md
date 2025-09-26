# Гайд по код‑ревью (Фаза 2)

Цель
- Упростить и ускорить ревью Фазы 2, зафиксировать критерии качества и чек‑листы для API (FastAPI), OpenAPI/TS‑клиента и Web (Next.js).

Что смотреть в коде
- Точка входа API и сборка роутов: `apps/api/app/api/main.py`
- Настройки/зависимости/ошибки: `apps/api/app/api/settings.py`, `apps/api/app/api/deps.py`, `apps/api/app/api/errors.py`
- DTO (Pydantic): `apps/api/app/api/schemas/*`
- Роуты (CRUD): `apps/api/app/api/routers/*` (`/health`, `/v1/life-areas`, `/v1/dreams`, `/v1/goals`, `/v1/projects`, `/v1/habits(+/logs)`, `/v1/tasks`, `/v1/attachments` (заглушка))
- OpenAPI экспорт и генерация клиента: `apps/api/scripts/export_openapi.sh`, `scripts/gen_client.sh` → `packages/shared/client/`
- Web (Next.js): `apps/web/app/*`, конфиги: `apps/web/package.json`, `apps/web/tsconfig.json`, `apps/web/next.config.js`

Обязательные проверки
- API локально поднимается (uvicorn), `/health` отвечает ok
- CRUD эндпойнты возвращают корректные коды и тела
- Пагинация limit/offset работает и соблюдает лимит
- OpenAPI экспортируется (apps/api/openapi.json актуален)
- CI (API & Web) зелёный: импорт API и сборка Web

Чек‑лист для API
1) Архитектура
- Роуты тонкие; бизнес‑логика по плану выносится в services/* (можно отметить TODO)
- Версионирование: префикс `/v1/*`
2) DTO/контракты
- Pydantic‑схемы согласованы с роутами; поля дат в ISO (дальше → datetime UTC)
- Статусы/enum — валидация (позже Literal/Enum)
3) Пагинация/фильтры
- limit ∈ [1..100], default 20; сортировка детерминирована (created_at desc)
4) Ошибки
- 404/422/400 корректны; формат ошибок унифицирован (целевой `code/message/details`)
5) Безопасность
- CORS=*, только для локалки — TODO сузить в прод; заглушка current_user понятна
6) ORM/SQLA
- Нет «глобальной» сессии; индексы Phase 1 покрывают основные запросы
7) Соответствие БД
- PK/FK/nullable совпадают с миграциями Phase 1 (см. LifeAreaLink PK, Memory.meta)

OpenAPI/TS‑клиент
- `/openapi.json` полон; `npx openapi-typescript` генерит клиент в `packages/shared/client/`
- План: фронт перейти на клиент вместо fetch

Web (Next.js)
- App Router, /health и /life-areas работают против API, есть обработка ошибок
- `NEXT_PUBLIC_API_BASE_URL` используется для всех запросов
- ESLint/TypeScript чистые на build

DX/CI
- Workflow `API & Web CI` — 2 независимых джоба (API и Web), кэш pip/npm
- Makefile: `api-dev`, `api-openapi`, `client-gen`, `web-dev`

Ручной тест (локально)
1) БД/миграции: `make bootstrap-local`
2) API: `make api-dev`, проверить `/health`, CRUD `/v1/*`
3) Web: `cd apps/web && npm ci && NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev`
4) OpenAPI: `cd apps/api && ./scripts/export_openapi.sh`
5) TS‑клиент: `./scripts/gen_client.sh` → `packages/shared/client/index.ts`

Рекомендации к доработке (последующие PR)
- Вынести логику в services/*, добавить юнит‑тесты CRUD
- Строгая валидация (Enum/regex), datetime с TZ, унифицированный формат ошибок
- Подключить сгенерированный TS‑клиент во фронт и React Query hooks
- Сузить CORS, добавить реальную auth (Phase 3)
