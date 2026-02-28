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