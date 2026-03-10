from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import MoodTag, UserAnimeMoodTag, Anime
from app.routers.anime_list import get_current_user_id
from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from sqlalchemy import select, func, Integer
from app.constants import SYSTEM_USER_ID, CONFIRMATION_THRESHOLD

router = APIRouter(prefix="/anime", tags=["tags"])

class TagResponse(BaseModel):
    id: UUID
    label: str
    slug: str
    vote_count: int
    is_suggested: bool
    confirmed: bool

class AnimeTagsResponse(BaseModel):
    confirmed: list[TagResponse]   # 3+ votes — full styling
    suggested: list[TagResponse]   # below threshold or is_suggested=True — lighter styling

class TagApplyRequest(BaseModel):
    tag_id: UUID

@router.get("/{anime_id}/tags", response_model=AnimeTagsResponse)
async def get_anime_tags(
    anime_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Returns tags in two groups: confirmed (3+ real community votes) and suggested.
    System user votes are excluded from the confirmation count — LLM suggestions
    don't count toward the threshold. Tags with only system votes appear as suggested
    with vote_count=0 (real votes only shown to users).
    """
    # Verify anime exists
    anime_result = await db.execute(select(Anime).where(Anime.id == anime_id))
    if not anime_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Anime not found")

    # Aggregate vote counts per tag for this anime
    vote_counts = await db.execute(
        select(
            MoodTag,
            func.count(UserAnimeMoodTag.user_id).label("total_votes"),
            func.sum(
                func.cast(UserAnimeMoodTag.user_id == SYSTEM_USER_ID, Integer)
            ).label("system_votes")
        )
        .outerjoin(UserAnimeMoodTag, (
            UserAnimeMoodTag.mood_tag_id == MoodTag.id) &
            (UserAnimeMoodTag.anime_id == anime_id)
        )
        .where(MoodTag.is_approved == True)
        .group_by(MoodTag.id)
        .having(func.count(UserAnimeMoodTag.user_id) > 0)
        .order_by(func.count(UserAnimeMoodTag.user_id).desc())
    )
    rows = vote_counts.all()

    confirmed = []
    suggested = []

    for tag, total_votes, system_votes in rows:
        system_votes = system_votes or 0
        real_votes = total_votes - system_votes
        is_confirmed = real_votes >= CONFIRMATION_THRESHOLD

        tag_data = TagResponse(
            id=tag.id,
            label=tag.label,
            slug=tag.slug,
            vote_count=real_votes,  # Show real community votes only
            is_suggested=tag.is_suggested,
            confirmed=is_confirmed,
        )
        if is_confirmed:
            confirmed.append(tag_data)
        else:
            suggested.append(tag_data)

    # Tags with only system (LLM) votes surface here as suggested with vote_count=0.
    # HAVING count > 0 checks total_votes including system votes, so LLM suggestions
    # are visible to the frontend with lighter styling until real users confirm them.
    return AnimeTagsResponse(confirmed=confirmed, suggested=suggested)


@router.post("/{anime_id}/tags", status_code=201)
async def apply_tag(
    anime_id: UUID,
    body: TagApplyRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Apply a mood tag to an anime. User must be authenticated.
    A user can tag an anime without it being on their list — flywheel entry point.
    """
    # Verify anime exists
    anime_result = await db.execute(select(Anime).where(Anime.id == anime_id))
    if not anime_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Anime not found")

    # Verify tag exists and is approved
    tag_result = await db.execute(
        select(MoodTag).where(MoodTag.id == body.tag_id, MoodTag.is_approved == True)
    )
    if not tag_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Tag not found")

    # Check if user already applied this tag to this anime
    existing = await db.execute(
        select(UserAnimeMoodTag).where(
            UserAnimeMoodTag.user_id == user_id,
            UserAnimeMoodTag.anime_id == anime_id,
            UserAnimeMoodTag.mood_tag_id == body.tag_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="You've already applied this tag")

    vote = UserAnimeMoodTag(
        user_id=user_id,
        anime_id=anime_id,
        mood_tag_id=body.tag_id,
    )
    db.add(vote)
    await db.commit()

    return {"message": "Tag applied"}


@router.delete("/{anime_id}/tags/{tag_id}", status_code=204)
# 204 is consistent with list entry delete endpoint
async def remove_tag(
    anime_id: UUID,
    tag_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Remove your tag vote from an anime."""
    result = await db.execute(
        select(UserAnimeMoodTag).where(
            UserAnimeMoodTag.user_id == user_id,
            UserAnimeMoodTag.anime_id == anime_id,
            UserAnimeMoodTag.mood_tag_id == tag_id,
        )
    )
    vote = result.scalar_one_or_none()
    if not vote:
        raise HTTPException(status_code=404, detail="Tag vote not found")

    await db.delete(vote)
    await db.commit()