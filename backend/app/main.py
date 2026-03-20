import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, anime_list, mal_import, anime, users, tags, mood_tags, vibe
from contextlib import asynccontextmanager
from app.scheduler import start_scheduler, scheduler
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.limiter import limiter

# Placement at top guarantees the cleanup happens at the right moment, even if the server crashes or gets a kill signal.
@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    # Everything above yield runs when app starts up. Everything below yield runs when app shuts down.
    yield
    # APScheduler stops cleanly, no orphaned jobs
    scheduler.shutdown()

app = FastAPI(title="Arcanum API", version="0.1.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(anime_list.router)
app.include_router(mal_import.router)
app.include_router(anime.router)
app.include_router(users.router)
app.include_router(tags.router)
app.include_router(mood_tags.router)
app.include_router(vibe.router)

@app.get("/")
async def root():
    return {"message": "Arcanum API is running"}

@app.get("/health")
async def health():
    return {"status": "ok"}