from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import User, UserAnimeRelationship, Anime, WatchStatus
from app.schemas import UserProfileResponse
from collections import Counter

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{username}", response_model=UserProfileResponse)
async def get_user_profile(
    username: str,
    db: AsyncSession = Depends(get_db)
):
    """User profile — list stats, genre breakdown, score distribution."""
    # Get user
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get all relationships with anime joined
    rel_result = await db.execute(
        select(UserAnimeRelationship, Anime)
        .join(Anime, UserAnimeRelationship.anime_id == Anime.id)
        .where(UserAnimeRelationship.user_id == user.id)
    )
    rows = rel_result.all()

    # Stats
    total = len(rows)
    completed = sum(1 for r, _ in rows if r.status == WatchStatus.completed)
    watching = sum(1 for r, _ in rows if r.status == WatchStatus.watching)
    plan_to_watch = sum(1 for r, _ in rows if r.status == WatchStatus.plan_to_watch)
    dropped = sum(1 for r, _ in rows if r.status == WatchStatus.dropped)

    scores = [r.computed_overall for r, _ in rows if r.computed_overall is not None]
    mean_score = round(sum(scores) / len(scores), 2) if scores else None

    # Genre breakdown
    genre_counter = Counter()
    for _, anime in rows:
        if anime.genres:
            for genre in anime.genres:
                genre_counter[genre] += 1
    genre_breakdown = [
        {"genre": genre, "count": count}
        for genre, count in genre_counter.most_common(10)
    ]

    # Score distribution (1-10)
    score_distribution = {str(i): 0 for i in range(1, 11)}
    for score in scores:
        if 1 <= score <= 10:
            score_distribution[str(score)] += 1

    return {
        "user_id": user.id,
        "username": user.username,
        "avatar_url": user.avatar_url,
        "stats": {
            "total": total,
            "completed": completed,
            "watching": watching,
            "plan_to_watch": plan_to_watch,
            "dropped": dropped,
            "mean_score": mean_score,
        },
        "genre_breakdown": genre_breakdown,
        "score_distribution": score_distribution,
    }