# Arcanum — Deploy Checklist

## Supabase Setup
- [ ] Enable pgvector extension: Dashboard → Database → Extensions → pgvector
- [ ] Enable pg_cron extension: Dashboard → Database → Extensions → pg_cron
- [ ] Set DATABASE_URL in Railway environment variables
- [ ] Set SECRET_KEY in Railway environment variables
- [ ] Set ANTHROPIC_API_KEY in Railway environment variables (Phase 2+)

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

## Environment Variables

### Vercel (Frontend)
| Variable | Value | Notes |
|----------|-------|-------|
| `API_URL` | `https://your-app.railway.app` | Server-side only. Used by server components. Never exposed to client bundle. |
| `NEXT_PUBLIC_API_URL` | `https://your-app.railway.app` | Client-side. Used by interactive components (tag voting, typeahead). Must have NEXT_PUBLIC_ prefix. |

Both point to the same Railway FastAPI URL. Two vars are required because Next.js server components cannot access NEXT_PUBLIC_ vars and client components cannot access private vars.

### Railway (Backend)
| Variable | Value | Notes |
|----------|-------|-------|
| `DATABASE_URL` | Supabase connection string | From Supabase dashboard → Settings → Database |
| `SECRET_KEY` | Random 32+ char string | JWT signing — generate with `openssl rand -hex 32` |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | From console.anthropic.com |
| `CORS_ORIGINS` | `https://your-app.vercel.app,http://localhost:3000` | Comma-separated. Include production Vercel domain. |

### Local Development (.env.local in frontend/, .env in backend/)
Frontend `.env.local`:
```
API_URL=http://localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Backend `.env`:
```
DATABASE_URL=postgresql+asyncpg://arcanum:arcanum@localhost:5432/arcanum
SECRET_KEY=your-local-secret-key
ANTHROPIC_API_KEY=sk-ant-...
```

## Post-Launch Security (Phase 3)

### Auth: localStorage → httpOnly cookies
Current: JWT stored in localStorage (XSS vulnerable but acceptable at launch scale)
Migration plan:
- Set up api.myarcanum.org custom domain on Railway (required for same-domain cookies)
- FastAPI sets httpOnly cookie on login, clears on logout
- Frontend removes all localStorage token management, uses `credentials: 'include'`
- Add CSRF protection (SameSite=Strict or fastapi-csrf-protect)
- Existing sessions invalidated — users log in again (acceptable at small scale)
- Do this before significant user growth, not before launch

### Rate limiting on /auth/register
- Add before public launch to prevent spam accounts
- Use slowapi (FastAPI rate limiting library)

### JWT expiration
- Verify tokens expire in reasonable time (check create_access_token in auth.py)