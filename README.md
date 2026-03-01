# Arcanum

A social anime tracking platform built around taste discovery — not just list management.

## The Problem with MAL and AniList
Existing anime trackers treat your watch history as a list. Arcanum treats it as a
taste fingerprint. Every anime you rate, tag, or track feeds a social graph that connects
you to people who actually watch the same way you do.

## What Makes It Different
- **Multi-axis scoring** — rate story, art, sound, characters, and enjoyment separately.
  Your overall score is computed from whichever axes you care about.
- **Community mood tagging** — tag anime with how it felt ("2am watch", "so bad its good",
  "peak fiction"). Tags aggregate into vibe-based discovery — browse by occasion, not genre.
- **Taste matching** — pgvector cosine similarity computes compatibility between users
  based on their full scoring history. "You and @user are 91% compatible."
- **Weighted social scores** — anime pages show what *your network* rated it,
  not just a global average.
- **Real-time presence** — see what your friends are watching right now.

## Tech Stack
| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router) → Vercel |
| Backend API | FastAPI (Python) → Railway |
| Database | PostgreSQL + pgvector → Supabase |
| Auth | JWT + bcrypt → Supabase Auth |
| Background Jobs | APScheduler + pg_cron |
| CI/CD | GitHub Actions |
| Anime Data | AniList GraphQL API |

## Architecture Highlights
- **pgvector** for taste vector similarity — each user's scoring history becomes
  a 512-dimension vector. Compatibility is a single SQL cosine distance query.
- **Community folksonomy** with LLM auto-categorization — users tag freely,
  tags roll up to parent mood categories for chart aggregation silently.
- **Flywheel design** — minimum user action (status + one mood tag) still feeds
  vibe browsing, taste vectors, and social matching.
- **Schema-first** — Alembic migrations, nullable score axes, computed_overall
  recalculated on every update.

## Status
🚧 Active development — Phase 1 of 5 complete

- ✅ Phase 0 — Foundation (FastAPI, Postgres, Auth, AniList seed)
- 🔄 Phase 1 — Core list features (CRUD, scoring, import tool)
- ⬜ Phase 2 — Mood tags + vibe browsing
- ⬜ Phase 3 — Social graph + taste matching
- ⬜ Phase 4 — Real-time presence
- ⬜ Phase 5 — LLM layer + public launch

Live demo available at Phase 2.

## Local Development
```bash
# Start Postgres + Redis
docker compose up -d

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# API docs at http://localhost:8000/docs
```

## Data Attribution
Anime metadata sourced from [AniList](https://anilist.co) via their public GraphQL API.