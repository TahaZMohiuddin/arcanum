# Arcanum — Deploy Checklist

## Supabase Setup
- [ ] Enable pgvector extension: Dashboard → Database → Extensions → pgvector
- [ ] Enable pg_cron extension: Dashboard → Database → Extensions → pg_cron
- [ ] Set DATABASE_URL in Railway environment variables
- [ ] Set SECRET_KEY in Railway environment variables
- [ ] Set OPENAI_API_KEY in Railway environment variables (Phase 2+)

## Railway Setup (FastAPI backend)
- [ ] Connect GitHub repo
- [ ] Set root directory to /backend
- [ ] Add environment variables from .env
- [ ] Verify health check at /health after deploy

## Vercel Setup (Next.js frontend)
- [ ] Connect GitHub repo
- [ ] Set root directory to /frontend
- [ ] Add NEXT_PUBLIC_API_URL pointing to Railway URL

## First Deploy Order
1. Supabase — enable extensions, run Alembic migrations against Supabase DB
2. Railway — deploy FastAPI, verify /health
3. Vercel — deploy Next.js, verify it hits Railway API