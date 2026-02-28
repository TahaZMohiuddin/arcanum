from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import UserAnimeRelationship, WatchStatus
from app.schemas import ListEntryCreate, ListEntryUpdate, ListEntryResponse
from app.auth import decode_token
from fastapi.security import OAuth2PasswordBearer
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional

router = APIRouter(prefix="/list", tags=["list"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> UUID:
    """Decode JWT and return current user's UUID."""
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return UUID(user_id)

def compute_overall(
    story: Optional[int],
    art: Optional[int],
    sound: Optional[int],
    characters: Optional[int],
    enjoyment: Optional[int]
) -> Optional[int]:
    """Average of whichever axes are filled in.
    Returns None if no axes are scored at all.
    """
    scores = [s for s in [story, art, sound, characters, enjoyment] if s is not None]
    if not scores:
        return None
    return round(sum(scores) / len(scores))

@router.post("/", response_model=ListEntryResponse, status_code=201)
async def add_to_list(
    entry: ListEntryCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Add an anime to the current user's list."""
    # Check if entry already exists
    result = await db.execute(
        select(UserAnimeRelationship).where(
            UserAnimeRelationship.user_id == user_id,
            UserAnimeRelationship.anime_id == entry.anime_id
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Anime already in your list")

    relationship = UserAnimeRelationship(
        user_id=user_id,
        anime_id=entry.anime_id,
        status=entry.status,
        currently_watching_ep=entry.currently_watching_ep,
        date_started=entry.date_started,
        date_completed=entry.date_completed,
        score_story=entry.score_story,
        score_art=entry.score_art,
        score_sound=entry.score_sound,
        score_characters=entry.score_characters,
        score_enjoyment=entry.score_enjoyment,
        computed_overall=compute_overall(
            entry.score_story, entry.score_art, entry.score_sound,
            entry.score_characters, entry.score_enjoyment
        ),
        rewatch_count=entry.rewatch_count or 0,
        rewatch_score=entry.rewatch_score,
    )
    db.add(relationship)
    await db.commit()
    await db.refresh(relationship)
    return relationship

@router.patch("/{entry_id}", response_model=ListEntryResponse)
async def update_entry(
    entry_id: UUID,
    updates: ListEntryUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing list entry. Only provided fields are changed."""
    result = await db.execute(
        select(UserAnimeRelationship).where(
            UserAnimeRelationship.id == entry_id,
            UserAnimeRelationship.user_id == user_id
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    # Apply only provided fields
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)

    # Recompute overall if any score axis was updated
    entry.computed_overall = compute_overall(
        entry.score_story, entry.score_art, entry.score_sound,
        entry.score_characters, entry.score_enjoyment
    )
    entry.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(entry)
    return entry

@router.delete("/{entry_id}", status_code=204)
async def delete_entry(
    entry_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Remove an anime from the current user's list."""
    result = await db.execute(
        select(UserAnimeRelationship).where(
            UserAnimeRelationship.id == entry_id,
            UserAnimeRelationship.user_id == user_id
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    await db.delete(entry)
    await db.commit()

@router.get("/", response_model=list[ListEntryResponse])
async def get_my_list(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get the current user's full anime list.
    # TODO: Add cursor-based pagination (keyset on created_at) when user lists grow large.
    # Offset pagination is worse for this use case — use created_at cursor instead.
    """
    result = await db.execute(
        select(UserAnimeRelationship).where(
            UserAnimeRelationship.user_id == user_id
        )
    )
    return result.scalars().all()