from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import Anime, UserAnimeRelationship
from app.schemas import AnimeResponse
from uuid import UUID

router = APIRouter(prefix="/anime", tags=["anime"])

@router.get("/{anime_id}", response_model=AnimeResponse)
async def get_anime(
    anime_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Anime detail page — title, synopsis, cover, genres, global average score."""
    result = await db.execute(
        select(Anime).where(Anime.id == anime_id)
    )
    anime = result.scalar_one_or_none()
    if not anime:
        raise HTTPException(status_code=404, detail="Anime not found")

    # Global average computed_overall across all users who scored it
    avg_result = await db.execute(
        select(func.avg(UserAnimeRelationship.computed_overall)).where(
            UserAnimeRelationship.anime_id == anime_id,
            UserAnimeRelationship.computed_overall.isnot(None)
        )
    )
    global_average = avg_result.scalar()

    return {
        "id": anime.id,
        "anilist_id": anime.anilist_id,
        "mal_id": anime.mal_id,
        "title": anime.title,
        "title_english": anime.title_english,
        "synopsis": anime.synopsis,
        "cover_url": anime.cover_url,
        "genres": anime.genres,
        "episode_count": anime.episode_count,
        "average_score": anime.average_score,
        "arcanum_score": round(global_average, 2) if global_average else None,
        "season": anime.season,
        "season_year": anime.season_year,
        "cached_vibe_tags": anime.cached_vibe_tags,
    }