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
- All score axes nullable
- Mood tags are Phase 2

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

## Session 6 — Mar 4-9, 2026

**Completed:**
- 8 new mood tags added (65 total): atmospheric, banger OP/ED, philosophical, damn good villain,
  I'm not okay rn, epic scope, cozy but dark, died from laughter
- System user created (seed_system_user.py)
  - Deterministic UUID: 00000000-0000-0000-0000-000000000001
  - is_active=False — cannot log in
  - hashed_password="SYSTEM_ACCOUNT_NO_LOGIN" — intentionally uncrackable
  - Idempotent seed script — safe to rerun across environments
- constants.py — centralized SYSTEM_USER_ID and CONFIRMATION_THRESHOLD
  - Both imported everywhere — no magic UUIDs scattered across files
- LLM auto-suggest job (app/llm_suggest.py)
  - Claude Haiku — cost efficient for 150 anime per run
  - Picks from existing 65 curated tags only — not an open-ended generator
  - Bulk prefetches: tag labels, anime needing suggestions, existing system suggestions
  - Batch commits every 25 anime — not 150 individual commits
  - Explicit tuple cast for duplicate check: {(row.anime_id, row.mood_tag_id) for row in ...}
  - System user ID on UserAnimeMoodTag is the signal for LLM suggestions — MoodTag.is_suggested NOT modified
  - asyncio.sleep(0.5) per anime for rate limiting
  - Validated against 5 anime — tags accurate (FMA:B → peak fiction, philosophical; HxH → certified classic, epic scope)
- Updated GET /anime/{id}/tags endpoint
  - Distinguishes system votes from real votes using func.cast(user_id == SYSTEM_USER_ID, Integer)
  - vote_count in response shows real community votes only — LLM votes invisible to users
  - Tags with only system votes surface as suggested with vote_count=0 — correct behavior
  - Removed outdated TODO comment — replaced with accurate explanation
- APScheduler updated
  - aggregate_vibe_tags: every 4 hours
  - run_llm_suggest: every 24 hours (cost consideration)
  - LLM suggestions picked up by aggregation job within 4 hours — no coordination needed
- VIBE_CLUSTERS updated with 8 new tags across appropriate clusters
- Note: slug for tag with '-' in label needs verification post-launch

**Decisions made:**
- is_suggested on MoodTag is reserved for future community proposal system
  (user-proposed tags start as is_suggested=True until approved by moderators)
  Currently unused — all 65 tags are hand-curated, defaults to False
- System user votes excluded from confirmation threshold — LLM suggestions
  don't count toward the 3-vote community threshold
- LLM suggest runs daily not hourly — cost consideration, new anime added infrequently
- Note for future development: vote_count in TagResponse shows real votes only.
  Frontend should display "X community votes" not just "X votes" to avoid confusion
  when system votes exist in DB but aren't shown.

**Lessons learned:**
- One file at a time when making multi-file changes — easier to track, fewer contradictions
- Wait ~60 seconds before pasting LLM job output — API calls take time
- psql pager (the ':' prompt) — use 'head -60' to avoid truncation

**Phase 2 backend status: COMPLETE**
- ✅ mood_tags + user_anime_mood_tags migration
- ✅ 65 curated tags seeded
- ✅ Tagging endpoints
- ✅ APScheduler aggregation job
- ✅ Vibe browse endpoints
- ✅ LLM auto-suggest job
- ✅ System user
- ✅ constants.py

**Next session starts with:**
- Next.js frontend scaffolding (/vibe as default authenticated route)
- Deploy to Vercel + Railway + Supabase after frontend is scaffolded — soft launch
- Phase 2 will be fully complete after deploy

## Session 7 — Mar 9-13, 2026

**Completed:**
- LLM auto-suggest prompt fix noted — Claude thinking out loud before JSON breaks parser.
  Fix when convenient: add "Output the JSON array immediately with no preamble, no reasoning,
  no 'let me reconsider'. Just the array." to end of prompt in llm_suggest.py
- Next.js frontend scaffolded at ~/arcanum/frontend
  - Next.js 16.1.6 with Turbopack, TypeScript, Tailwind, App Router
  - Fonts: Syne (body/UI) + DM Serif Display (headings) via next/font/google
  - globals.css: dark theme CSS variables, scroll-row class, tag-pill class, page-container class
  - layout.tsx: font variables, metadata ("Your Anime Taste Fingerprint")
  - next.config.ts: AniList image domains (cdn.anilist.co, s4.anilist.co)
  - .env.local: API_URL=http://localhost:8000
- src/lib/types.ts: TypeScript interfaces matching FastAPI response schemas
  (TagResponse, AnimeCard, VibeCluster)
- /vibe page built and polished (src/app/vibe/page.tsx)
  - Server component, fetches from process.env.API_URL (not hardcoded localhost)
  - revalidate: 14400 (4hr cache matches aggregation job schedule)
  - CLUSTER_SUBTITLES map — editorial one-liners per cluster
    ("For when sleep isn't coming anyway", "You asked for this", "You will not be okay")
  - TODO comment: time-based cluster ordering Phase 4+
- VibeCluster component (src/components/VibeCluster.tsx)
  - DM Serif Display headings, cluster subtitles in --text-secondary
  - Scroll arrows using useRef + scrollBy (440px increments, smooth)
  - "see all →" link to /vibe/{cluster.id}
- AnimeCard component (src/components/AnimeCard.tsx)
  - w-48 h-72 (192×288px) — proper 2:3 anime poster ratio
  - Tag pills always visible at rest (top 3), glow effect via box-shadow
  - Score badge top-right, high opacity backdrop
  - Gradient overlay at bottom of cover art
  - flex-col + flex-1 on footer for consistent row heights
  - items-stretch on scroll row for even card heights
- Ran LLM suggest on 150 anime + aggregation job
  - ~400 suggestions inserted across batches
  - Parse failures noted (Claude thinking out loud) — prompt fix deferred
  - All clusters populated with real data after aggregation

**Decisions made:**
- Tags visible at rest on cards (not hidden behind hover) — Opus pushed back, correct
- /vibe is default authenticated route (post-login landing page)
- process.env.API_URL for server components (not NEXT_PUBLIC_ — keeps backend URL out of client bundle)
- Japanese immersion tags (beginner friendly Japanese, clear dialogue, JLPT N4 level etc.)
  deferred to post-launch — good niche differentiator for immersion learning community,
  confirm audience exists before adding
- Time-based cluster ordering deferred to Phase 4 — TODO comment in vibe/page.tsx

**Pre-deploy checklist (complete before pushing to Vercel/Railway/Supabase):**
- [ ] Set API_URL in Vercel env vars → Railway FastAPI URL
- [ ] Add production Vercel domain to FastAPI CORS allow_origins in main.py
- [ ] Set DATABASE_URL in Railway → Supabase production Postgres
- [ ] Set ANTHROPIC_API_KEY in Railway env vars
- [ ] Run Alembic migrations against production Supabase DB
- [ ] Run seed scripts against production (anime + mood tags + system user)
- [ ] grep -r "localhost" ~/arcanum/ to catch any hardcoded URLs

**Lessons learned:**
- Hard refresh (Ctrl+Shift+R) required after backend data changes — Next.js caches fetch responses
- next/image requires remotePatterns config for external domains or images fail silently
- items-stretch on flex row + flex-col + flex-1 on card = consistent row heights
- Frontend polish is open-ended — timebox it, get to "screenshot worthy" then move on

**/vibe page status: COMPLETE — screenshot worthy**

**Next session starts with:**
- /anime/[id] detail page — cover art large, synopsis, tags confirmed/suggested split, score
- /profile/[username] page — stats, genre breakdown, score distribution
- /import page — MAL file upload
- Login/register pages
- Then deploy using pre-deploy checklist above
- Phase 2 fully complete after deploy

**Architecture reminders:**
- Next.js is rendering layer only — all data from FastAPI, no Server Actions for mutations
- Server components fetch using process.env.API_URL
- Client components only when interactive (tag voting, typeahead)
- CORS in main.py must include production Vercel domain before deploy

## Session 8 — Mar 13-18, 2026

**Completed:**
- /anime/[id] detail page
  - Server component, fetches anime + tags in parallel (Promise.all)
  - TagSection client component — confirmed/suggested split, optimistic UI on vote
  - dangerouslySetInnerHTML replaced with plain text rendering (security)
  - revalidate: 3600 for anime data, revalidate: 0 for tags (always fresh)
- /profile/[username] page
  - StatsCharts client component — hand-built CSS charts, no library
  - Score distribution: colored bars per score (red→green→purple), count labels
  - Genre breakdown: 8 colors cycling, horizontal bars
  - Status breakdown: stacked bar with semantic colors
  - "Taste Fingerprint" heading
  - TODO Phase 3+: "Your Vibe" identity section, top-rated anime row, mood donut chart
- Login/register pages
  - Auto-login after register
  - OAuth2PasswordRequestForm — sends x-www-form-urlencoded not JSON
  - Password minimum 8 characters (backend Pydantic validator)
- src/lib/auth.ts — localStorage token management
  - TODO Phase 3: migrate to httpOnly cookies (requires api.myarcanum.org custom domain)
- NavBar component
  - Sticky, backdrop blur, auth-aware
  - "Arcanum" in pill-text purple (brand mark)
  - "Discover", username in pill-text, "Import", "Disappear"
  - removeUsername called on logout (fixes broken state bug)
  - TODO Phase 3+: logo icon/motif (commissioned artist)
  - TODO Phase 4+: notification dot for social features
- /import page — MAL + AniList toggle
  - AniList default (target audience skews AniList)
  - AniList: username-based API fetch, no file needed, direct anilist_id matching
  - MAL: XML file upload, 5MB client-side limit, defusedxml on backend
  - try-catch on all fetches, file size validation, network error handling
  - Result: imported/skipped/unmatched counts, unmatched titles as pills
  - "Start browsing →" and "View your list →" CTAs
- AniList import backend (POST /import/anilist)
  - GraphQL MediaListCollection query with pagination
  - Same bulk-fetch pattern as MAL import
  - Direct anilist_id matching — no ID mapping problem
  - REPEATING status → watching
- /vibe/[slug] drill-down page
  - Grid layout using existing AnimeCard component
  - Cluster subtitle carries over from browse page
  - "← All vibes" breadcrumb navigation
  - notFound() on invalid slugs
  - revalidate: 14400 matches aggregation schedule
  - TODO Phase 3+: sort options, pagination, related clusters sidebar

**Bug fixed:**
- computed_overall Float migration caused KeyError in score_distribution dict
  Fix: str(int(round(score))) before dict lookup
  Lesson: grep codebase for all column consumers when changing column type

  **Nav copy refined:**
- Browse → Discover
- Sign in → Return  
- Get started → Enter
- Sign out → Disappear

**UI/Branding TODOs (discussed, not yet implemented):**
- Tag pills on AnimeCard should link to /vibe/{tag-slug} for drill-down navigation
- Profile page: genre pill spacing from synopsis needs breathing room on detail page
- Suggested tags section on detail page needs more vertical spacing from synopsis
- Cluster subtitles should appear on drill-down page (done) — verify on individual tag slugs
- Time-based cluster ordering — Late Night Watch surfaces at top during late hours, Watch With Friends on Fridays, etc (Phase 4+)
- Japanese immersion tags — "N4 Japanese", "beginner friendly" etc. (post-launch tag batch)
- Guest browsing — vibe page accessible without login, conversion at save/tag moment
- Power follow — weight multiplier on follows table for trusted taste sources (Phase 4+)
- Tag pills as links throughout the app for consistent drill-down navigation
- Scroll arrows only functional when cluster has more anime than viewport width — not a bug
- next.config.ts image domains — cdn.anilist.co and s4.anilist.co configured ✅

**Decisions made:**
- localStorage for auth at launch — httpOnly cookies deferred to Phase 3
  (cross-domain Vercel/Railway cookie issue, zero users at launch)
- AniList import as username fetch not file upload — simpler, no export needed
- AniList default on import page — target audience skews AniList
- [id] is Next.js dynamic route syntax — matches any value, passes as param
- params is a Promise in Next.js 16 — always await before accessing properties
- Hand-built CSS charts over Recharts/Chart.js — no dependency, full style control
- Syne font for body, DM Serif Display for headings — replaces default Geist to avoid Vercel template look
- Typographic logo at launch, commission human artist after traction
- AniList API terms allow complementary services with sustained integration — AniList OAuth login planned for Phase 4+ to strengthen positioning
- Vibe browse tiebreaker: when tag votes are tied, sort by Anime.average_score.desc() — higher rated anime surface first among equally-voted entries

**Security hardening done:**
- Password minimum 8 chars (Pydantic validator)
- defusedxml for MAL XML parsing (already done Phase 1)
- Login endpoint uses form data not JSON (OAuth2PasswordRequestForm)
- CORS via environment variable (not hardcoded)

**Post-launch security TODO (in DEPLOY.md):**
- httpOnly cookies migration (Phase 3)
- Rate limiting on /auth/register (before public launch)

**Phase 2 frontend status: COMPLETE**

**Next session: DEPLOY**
Follow pre-deploy checklist in DEPLOY.md:
1. grep -r "localhost" ~/arcanum/
2. Set up Supabase project
3. Run migrations against Supabase
4. Deploy backend to Railway
5. Deploy frontend to Vercel
6. Set all environment variables
7. Run seed scripts against production
8. Test end to end

## Deployment Fixes — Session 9 (Mar 19-20, 2026)

**Context:** First production deployment to Supabase. Took multiple sessions to resolve.
Documenting every fix so future deployments take minutes not hours.

### Fix 1: load_dotenv() unreliable without explicit path
Problem: bare `load_dotenv()` didn't reliably find `.env` when scripts ran from
different working directories. Shell `export` couldn't override it.
Fix in `database.py` and `alembic/env.py`:
```python
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'), override=True)
```
Key lesson: always use explicit path + override=True with load_dotenv.

### Fix 2: Supabase strips +asyncpg from connection string
Problem: Supabase returns `postgresql://` — dotenv was stripping the `+asyncpg`
so SQLAlchemy loaded psycopg2 (sync) instead of asyncpg (async).
Fix in `database.py`:
```python
DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
```
Key lesson: never rely on .env preserving +asyncpg. Always convert programmatically.
This is a known Supabase + FastAPI issue.

### Fix 3: Seed scripts had their own engine creation
Problem: all three seed scripts duplicated database connection logic.
When Fix 1/2 were needed, we had to fix 4 files instead of 1.
Fix: removed local engine creation from seed_anime.py, seed_mood_tags.py,
seed_system_user.py. All now import from app.database:
```python
sys.path.insert(0, os.path.dirname(__file__))
from app.database import AsyncSessionLocal
```
Key lesson: single source of truth for DB connections. Never create engines
in scripts — always import from app.database.

### Fix 4: Alembic uses SYNC_DATABASE_URL, not DATABASE_URL
Problem: Alembic env.py reads SYNC_DATABASE_URL (sync psycopg2) while FastAPI
reads DATABASE_URL (async asyncpg). Hours wasted checking wrong variable.
Key lesson: two separate env vars, two separate drivers.
- DATABASE_URL → FastAPI (postgresql+asyncpg://)
- SYNC_DATABASE_URL → Alembic (postgresql://)
Always check which var a tool actually reads before debugging.

### Fix 5: Supabase auth.users conflicts with CREATE TABLE users
Problem: Supabase has built-in auth schema with its own users table.
Postgres search_path included auth schema, causing DuplicateTable errors.
Fix — run once in Supabase SQL Editor:
```sql
ALTER ROLE postgres SET search_path TO public;
```
Key lesson: always set search_path to public for Supabase app connections.
URL-based ?options=-csearch_path%3Dpublic doesn't work with Alembic
(configparser chokes on % character).

### Fix 6: Broken Alembic migration — add_mal_id recreated all tables
Problem: migration a0c1890c4c6d_add_mal_id_to_anime_table.py was generated
against an empty database. Instead of adding mal_id column, it had CREATE TABLE
for users, anime, and user_anime_relationships — duplicating previous migrations.
Fix: replaced upgrade() with:
```python
def upgrade() -> None:
    op.add_column('anime', sa.Column('mal_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_anime_mal_id'), 'anime', ['mal_id'], unique=False)
```
Key lesson: ALWAYS read every auto-generated migration before running it.
alembic revision --autogenerate diffs models against DB state — if DB was
empty when generated, migration captures full schema instead of diff.
Never trust autogenerate blindly.

### Deployment command sequence that works:
```sql
-- Run in Supabase SQL Editor first:
ALTER ROLE postgres SET search_path TO public;
DROP TABLE IF EXISTS user_anime_relationships CASCADE;
DROP TABLE IF EXISTS anime CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS alembic_version CASCADE;
DROP TYPE IF EXISTS watchstatus CASCADE;
```
```bash
# Then from terminal with Supabase URL in .env:
alembic upgrade head
python seed_anime.py
python seed_mood_tags.py
python seed_system_user.py
```

### Files modified for deployment:
- backend/app/database.py — explicit dotenv path, async driver conversion
- backend/alembic/env.py — explicit dotenv path, SYNC_DATABASE_URL
- backend/seed_anime.py — imports AsyncSessionLocal from database.py
- backend/seed_mood_tags.py — imports AsyncSessionLocal from database.py
- backend/seed_system_user.py — imports AsyncSessionLocal from database.py
- backend/alembic/versions/a0c1890c4c6d — fixed to add_column not create_table
- backend/.env — SYNC_DATABASE_URL added, both URLs point to Supabase during deploy

### On hardcoding .env for deployment:
The .env swap is a one-time local pain. Railway injects environment variables
directly into the running process — you never touch .env for production.
For future Supabase reseeds, swap .env temporarily, run seeds, swap back.
Consider writing a deploy.sh script that automates this swap.

### Additional lesson not in Opus summary:
- alembic stamp base then upgrade head is WRONG if tables partially exist
  Use stamp {revision_hash} to tell Alembic "DB is at this state" without
  running migrations. Only use stamp base + upgrade head on truly empty DB.
- Supabase Table Editor doesn't always show tables immediately after creation —
  use SQL Editor SELECT tablename FROM pg_tables WHERE schemaname='public'
  to verify actual DB state. Never trust the Table Editor UI alone.
- Database reset in Supabase does NOT always clear everything — auth schema
  tables survive. Always run explicit DROP TABLE statements after reset.