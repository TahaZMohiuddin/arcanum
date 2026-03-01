# Arcanum — Progress Log

## Session 1 — Feb 26, 2026
**Completed:** Phase 0 entirely in one session.
- Monorepo structure created
- Docker Compose running Postgres (pgvector) + Redis locally
- FastAPI backend scaffolded with health check endpoints
- Alembic migrations configured
- Users table + anime table created
- JWT auth: register + login endpoints working with bcrypt
- AniList GraphQL seed script — 500 anime in database
- GitHub repo live: github.com/TahaZMohiuddin/arcanum

**Decisions made:**
- Dropped Celery → APScheduler + pg_cron (simpler, debuggable)
- Dropped Redis at launch → add only when latency data justifies it
- Dropped Spring Boot parallel project
- Supabase Auth + hosted Postgres at deploy time
- Flywheel entry point = status + mood tags, multi-axis scoring is opt-in

## Session 2 — Feb 27, 2026
**Completed:** Phase 1 started.
- user_anime_relationships table + migration (core entity of the app)
- WatchStatus enum: watching/completed/dropped/plan_to_watch/on_hold
- Fixed empty Alembic migration artifact
- DEPLOY.md created — Supabase extension checklist (pgvector + pg_cron)
- GitHub Actions CI/CD: 3 pytest tests passing on every push
- TODO in test_api.py: replace docs test with test_create_relationship
  and test_computed_overall once CRUD endpoints are built
- python-multipart added to requirements.txt
- conftest.py created — runs Base.metadata.create_all() before tests
  so CI Postgres has tables
- CI/CD fully green and  now catches missing dependencies and schema issues on every push

**Next session starts with:**
- CRUD endpoints for list management (add/update/delete anime to list)
- Router: backend/app/routers/list.py
- Schemas for UserAnimeRelationship request/response
- computed_overall calculation logic
- Then: MAL/AniList import tool

**Architecture reminders:**
- Status is the only required field on a list entry
- Mood tags live in user_anime_mood_tags (Phase 2) — separate FKs,
  NOT tied to user_anime_relationships
- taste_vector added in Phase 3 migration, not now
- Reference animelist-system-design artifact for full picture

**Lessons learned:**
- Comments inside YAML `options:` blocks get passed to Docker as arguments. Put comments above the block instead
- CI has no .env and no migrations. Conftest.py handles schema, env vars go in the workflow yaml

## Session 3 — Feb 28, 2026
**Completed:**
- CRUD endpoints for list management (anime_list.py router)
  - POST /list/ — add anime to list (status only required)
  - PATCH /list/{entry_id} — partial update, any subset of fields
  - DELETE /list/{entry_id} — remove entry
  - GET /list/ — fetch full user list (TODO: cursor pagination later)
- ListEntryCreate, ListEntryUpdate, ListEntryResponse schemas
- compute_overall() — averages whichever score axes are filled in
- Pydantic field_validator — scores constrained to 1-10, nulls allowed
- Renamed list.py → anime_list.py to avoid Python builtin shadow
- Updated tests: 4 passing, replaced placeholder with real business logic tests
- Manually verified via /docs: status-only entry works, score validation works

**Decisions made:**
- FastAPI checks auth before Pydantic validates body (401 before 422)
- Pagination deferred. I left a TODO comment on GET /list/ endpoint
- Score range is 1-10 (not 1-100) — keeping it simple for now

**Next session starts with:**
- MAL/AniList import tool — parse export XML/JSON into user_anime_relationships
- Then: anime detail endpoint (GET /anime/{id}) with global average scores
- Then: user profile endpoint (GET /users/{username})

**Architecture reminders:**
- compute_overall lives in the router, not the model
- All score axes nullable — never required
- Mood tags are Phase 2 — don't build them yet

## Session 4 — Mar 1, 2026

**Completed:**
- mal_id column added to anime table via Alembic migration
- Seed script updated to pull idMal from AniList GraphQL (idMal field)
- 500 anime re-seeded with mal_id populated
- MAL import tool (POST /import/mal)
  - defusedxml for security (entity expansion attack prevention)
  - Bulk queries with .in_(). 2 DB calls regardless of list size.
  - MAL status → WatchStatus enum mapping
  - Import summary response: imported, skipped, unmatched_count, unmatched_titles
  - MAL export validation (root tag check)
  - datetime import moved to module level (Opus feedback)
  - TODO comment: score_source enum for distinguishing imported vs multi-axis scores
- Validated against my own MAL export: 99 imported, 106 unmatched (expected), 0 errors

**Decisions made:**
- mal_id over title matching. Title matching breaks and will drive away power users or something.
- defusedxml for any user-uploaded XML
- computed_overall set directly from MAL single score on import (since MAL and AniList do not have multi-axis available)

**Lessons learned:**
- Always check DB state before debugging Alembic: `docker exec -it arcanum_db psql -U arcanum -d arcanum -c "\dt"`
- If tables missing, run `alembic upgrade head` before anything else
- Never rely on Base.metadata.create_all() for local dev
- Locally need to re-authenticate after Docker volume resets for testing purposes

**Next session starts with:**
- Anime detail endpoint: GET /anime/{id} — title, synopsis, cover, global average scores
- User profile endpoint: GET /users/{username} — list, stats, genre breakdown
- Then Phase 1 is complete and I will assess readiness for Phase 2

**Architecture reminders:**
- Score axes are all nullable — computed_overall is only populated if axes exist or on import
- mal_id on anime table is the import lookup key while id is the ID off AniList's API
- Bulk pre-fetch pattern. Use .in_() before loops. Never query inside loops. Why am I saying this? Because I'm a lost junior dev.