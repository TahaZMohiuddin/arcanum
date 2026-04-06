from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Follow, UserAnimeRelationship, Anime, User, WatchStatus
from app.routers.anime_list import get_current_user_id
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/feed", tags=["feed"])


class FeedEntry(BaseModel):
    # User who performed the activity
    username: str
    avatar_url: Optional[str]
    # TODO Phase 3.5: add taste_match: Optional[float] = None here
    # when taste_compatibility_cache exists — JOIN is already designed for it

    # Anime
    anime_id: UUID
    anime_title: str
    anime_title_english: Optional[str]
    anime_cover_url: Optional[str]

    # Activity
    status: str
    computed_overall: Optional[float]  # nullable — user may not have scored
    updated_at: datetime

    model_config = {"from_attributes": False}


class FeedResponse(BaseModel):
    items: list[FeedEntry]
    next_cursor: Optional[str]  # ISO timestamp — pass as ?before= on next request

# TODO: Add index on UserAnimeRelationship.updated_at for feed query performance.
# Feed sorts by updated_at DESC and filters with updated_at < cursor.
# Full table scan is fine at launch scale — add index before 1000+ users.
@router.get("/", response_model=FeedResponse)
async def get_feed(
    before: Optional[str] = Query(None, description="Cursor — ISO timestamp. Returns entries older than this."),
    limit: int = Query(20, ge=1, le=50),
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Personal activity feed — recent anime activity from users in your circle.
    
    Cursor-based pagination on updated_at. Pass next_cursor as ?before= for next page.
    Returns all activity types (completed, watching, dropped, scored) — frontend decides styling.
    
    TODO Phase 3.5: JOIN taste_compatibility_cache to add taste_match per user.
    TODO Phase 3.5: JOIN user_anime_mood_tags to add mood_tags_applied per entry.
    Both are additive changes — response schema already has placeholder comments.
    """
    # Parse cursor
    cursor_dt = None
    if before:
        try:
            cursor_dt = datetime.fromisoformat(before.replace("Z", "+00:00"))
        except ValueError:
            cursor_dt = None

    # Single query — follows + user_anime_relationships + anime + users
    # No N+1: all data fetched in one JOIN
    query = (
        select(
            User.username,
            User.avatar_url,
            Anime.id.label("anime_id"),
            Anime.title.label("anime_title"),
            Anime.title_english.label("anime_title_english"),
            Anime.cover_url.label("anime_cover_url"),
            UserAnimeRelationship.status,
            UserAnimeRelationship.computed_overall,
            UserAnimeRelationship.updated_at,
        )
        .join(Follow, Follow.following_id == User.id)
        .join(UserAnimeRelationship, UserAnimeRelationship.user_id == User.id)
        .join(Anime, Anime.id == UserAnimeRelationship.anime_id)
        .where(Follow.follower_id == current_user_id)
        .order_by(UserAnimeRelationship.updated_at.desc())
        .limit(limit + 1)  # fetch one extra to determine if next page exists
    )

    if cursor_dt:
        query = query.where(UserAnimeRelationship.updated_at < cursor_dt)

    result = await db.execute(query)
    rows = result.all()

    # Determine next cursor
    has_more = len(rows) > limit
    items = rows[:limit]

    next_cursor = None
    if has_more and items:
        next_cursor = items[-1].updated_at.isoformat()

    feed_items = [
        FeedEntry(
            username=row.username,
            avatar_url=row.avatar_url,
            anime_id=row.anime_id,
            anime_title=row.anime_title,
            anime_title_english=row.anime_title_english,
            anime_cover_url=row.anime_cover_url,
            status=row.status.value if isinstance(row.status, WatchStatus) else row.status,
            computed_overall=row.computed_overall,
            updated_at=row.updated_at,
        )
        for row in items
    ]

    return FeedResponse(items=feed_items, next_cursor=next_cursor)