from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import MoodTag
from app.routers.tags import TagResponse

router = APIRouter(prefix="/tags", tags=["tags"])

# tags.py is per anime tag operations; mood_tags.py is the global tag catalog

@router.get("/", response_model=list[TagResponse])
async def list_tags(
    db: AsyncSession = Depends(get_db)
):
    """Returns all approved tags ordered by usage_count.
    Used for typeahead search on the frontend — call once on page load and filter client-side.
    """
    result = await db.execute(
        select(MoodTag)
        .where(MoodTag.is_approved == True)
        .order_by(MoodTag.usage_count.desc())
    )
    tags = result.scalars().all()

    return [
        TagResponse(
            id=tag.id,
            label=tag.label,
            slug=tag.slug,
            vote_count=tag.usage_count,
            is_suggested=tag.is_suggested,
            # confirmed=True for all. Typeahead shows available tags, not vote status like in tags.py
            confirmed=True,
        )
        for tag in tags
    ]