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

## Session 4 continued — Mar 1, 2026

**Completed:**
- Anime detail endpoint: GET /anime/{anime_id}
  - Returns title, synopsis, cover, genres, episode count, AniList average score
  - arcanum_score: global average of computed_overall across all Arcanum users
  - Public endpoint. No auth required
- User profile endpoint: GET /users/{username}
  - Returns stats, genre breakdown (top 10), score distribution (1-10)
  - Public endpoint. No auth required
- Proper nested response schemas: UserStats, GenreCount, UserProfileResponse
  - No more loose `dict` types
- TODO comment added: refactor status counts to SQL aggregations when list sizes grow

**Decisions made:**
- arcanum_score not global_arcanum_average. This is shorter, and the frontend will type it constantly
- Genre breakdown stays Python (JSONB array is harder to aggregate in SQL)
- Status counts and mean_score are Python loops for now. This is acceptable under 500 entries. We'll work on this later. Spending time optimizing Postgres with 0 users is like kind of a waste of time.

**Phase 1 status: COMPLETE**
- ✅ user_anime_relationships table + migration
- ✅ CRUD endpoints with score validation
- ✅ MAL import tool
- ✅ CI/CD green
- ✅ Anime detail endpoint
- ✅ User profile endpoint with real taste data

**Next session starts with Phase 2:**
- Alembic migration: mood_tags + user_anime_mood_tags tables
  - is_approved boolean (default true for seeded tags)
  - is_suggested boolean (default false, marks LLM-generated suggestions)
  - No category enum
  - parent_mood_id self-referential FK (nullable, for chart rollup)
- Hand-tag top 50 anime manually
- LLM auto-suggest next 150 with is_suggested=true (This is still being debated but whateverrrrrrrr)
- Next.js frontend scaffolding -- first pages: home, anime detail, user profile
- Display threshold: 3+ user applications to graduate suggested → confirmed (query layer, not DB)

**Architecture reminders:**
- Suggested tags render with lighter visual treatment until 3+ users confirm them
- No user-created tags at launch — curated vocabulary only
- arcanum_score on anime detail page shows platform average vs AniList average
- User profile stats page will eventually need SQL aggregations (TODO comment in users.py)

## Session 5 — Mar 4-6, 2026

**Completed:**
- mood_tags + user_anime_mood_tags Alembic migration
  - is_approved (bool, default true), is_suggested (bool, default false)
  - parent_mood_id self-referential FK — silent, for chart rollup only, never exposed during tagging
  - No category enum — vibe browse clusters are presentation layer, not DB constraints
  - anime_id index on user_anime_mood_tags for efficient "all tags for this anime" queries
  - ondelete CASCADE on user_id, anime_id, mood_tag_id FKs
  - UniqueConstraint on (user_id, anime_id) in user_anime_relationships
  - computed_overall changed from Integer to Float — preserves signal (7.8 vs 8.0 matters for taste matching)
- 58 curated mood tags seeded (seed_mood_tags.py)
  - Bulk fetch pattern — 1 query, not 60
  - Idempotent — safe to rerun
- Tagging endpoints (POST/DELETE /anime/{id}/tags, GET /anime/{id}/tags)
  - Confirmed/suggested split in response — frontend never counts votes
  - CONFIRMATION_THRESHOLD = 3 votes to graduate suggested → confirmed
  - LLM-suggested tags graduate to confirmed at 3+ votes (is_suggested doesn't block graduation)
  - 204 on DELETE, consistent with list entry delete
  - TODO: LLM-suggested tags with zero votes won't surface in GET (HAVING count > 0 filters them). Needs union or separate query when LLM suggest is added.
- GET /tags/ endpoint for typeahead
  - Separate router (mood_tags.py) to avoid routing conflict with /anime/{id}/tags
- APScheduler vibe tag aggregation job (scheduler.py)
  - Runs every 4 hours
  - Single bulk SELECT across all anime, Python grouping with defaultdict — no N+1
  - Updates cached_vibe_tags JSONB on anime table
  - Updates usage_count on mood_tags table
  - usage_count is pg_cron/scheduler maintained — never increment in application code
  - Lifespan context manager (FastAPI 0.93+ pattern, replaces deprecated @app.on_event)
  - TODO Phase 4: presence TTL cleanup job lives here. DELETE FROM presence WHERE updated_at < now() - interval '30 minutes'. Frontend pings /presence every ~2 min while watching to keep record fresh.
- Vibe browse endpoints (GET /vibe/, GET /vibe/{slug})
  - 8 predefined clusters — presentation layer only, not stored in DB
  - Bulk prefetch all tag IDs in one query before cluster loop
  - Drill-down handles both cluster IDs and individual tag slugs
  - top_tags reads from cached_vibe_tags JSONB — no extra join
  - anilist_score named honestly (not arcanum_score — that requires join to user_anime_relationships)
  - TODO: Cache entire GET /vibe/ response with 4hr TTL if browse page feels slow. Response only changes when aggregation job runs.
- Validated full pipeline: tag applied → aggregation job → cache updated → vibe browse reads from cache

**Decisions made:**
- APScheduler over pg_cron locally. Migration path to pg_cron is clean — core logic is pure SQL.
  APScheduler → pg_cron migration: extract SELECT/UPDATE into single UPDATE...FROM subquery,
  schedule via SELECT cron.schedule(). Python grouping logic disappears. One SQL statement:
  UPDATE anime SET cached_vibe_tags = (
      SELECT jsonb_object_agg(slug, jsonb_build_object('label', label, 'count', cnt))
      FROM (
          SELECT mt.slug, mt.label, count(*) as cnt
          FROM user_anime_mood_tags uamt
          JOIN mood_tags mt ON mt.id = uamt.mood_tag_id
          WHERE uamt.anime_id = anime.id
          GROUP BY mt.slug, mt.label
      ) sub
  )
  WHERE id IN (SELECT DISTINCT anime_id FROM user_anime_mood_tags);
- LLM auto-categorization from artifact superseded by is_suggested approach — LLM suggests tags per anime, not categorizes user-created tags
- /vibe is the default authenticated route in Next.js (post-login landing page)
- Column() style throughout models.py — do not mix with Mapped[] style until full migration

**Lessons learned:**
- Rule: bulk fetch with .in_() before ANY loop. No DB calls inside loops. Ever.
- Always paste models.py before writing migrations — autogenerate only detects what's in models
- Pylance "could not be resolved" warnings are VS Code config, not real errors. Fix: Ctrl+Shift+P → Python: Select Interpreter → point to venv. Yes, I am actually this dumb.

**Next session starts with:**
- LLM auto-suggest job — needs Anthropic API key in .env
- Next.js frontend scaffolding
- Deploy to Vercel + Railway + Supabase — soft launch

**Architecture reminders:**
- cached_vibe_tags JSONB on anime table is the read cache for vibe browse — never join to mood_tags on browse queries
- usage_count on mood_tags is scheduler-maintained only
- Vibe browse clusters are defined in vibe.py VIBE_CLUSTERS — presentation layer, not DB
- confirmed = vote_count >= 3, regardless of is_suggested. LLM tags graduate like any other.
- parent_mood_id is for chart rollup aggregation only — never expose during tagging