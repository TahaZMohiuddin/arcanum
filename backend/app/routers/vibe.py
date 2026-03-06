from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import Anime, MoodTag, UserAnimeMoodTag
from pydantic import BaseModel
from uuid import UUID
from typing import Optional

router = APIRouter(prefix="/vibe", tags=["vibe"])

VIBE_CLUSTERS = [
    {
        "id": "late-night",
        "label": "Late Night Watch",
        "slugs": ["2am-watch", "dreamlike", "melancholy", "lonely", "quietly-devastating"],
    },
    {
        "id": "watch-together",
        "label": "Watch With People",
        "slugs": ["watch-with-friends", "hype-watch", "chaotic-energy", "so-bad-its-good", "binge-worthy"],
    },
    {
        "id": "emotional",
        "label": "Prepare to Cry",
        "slugs": ["good-cry", "emotionally-devastating", "youll-ugly-cry", "emotional-gut-punch-finale", "bittersweet"],
    },
    {
        "id": "chill",
        "label": "Low Effort High Reward",
        "slugs": ["cozy", "comfort-rewatch", "background-watch", "wholesome", "comfort-food-anime"],
    },
    {
        "id": "prestige",
        "label": "Peak Fiction",
        "slugs": ["peak-fiction", "certified-classic", "ahead-of-its-time", "rewarding-payoff", "sticks-the-landing"],
    },
    {
        "id": "hidden",
        "label": "Underrated & Hidden",
        "slugs": ["hidden-gem", "underrated", "better-than-its-reputation", "aged-like-wine", "grows-on-you"],
    },
    {
        "id": "intense",
        "label": "Edge of Your Seat",
        "slugs": ["anxiety-inducing", "nerve-wracking", "unsettling", "existential-dread", "makes-you-stare-at-the-ceiling"],
    },
    {
        "id": "aesthetic",
        "label": "Style & Vibes",
        "slugs": ["visually-stunning", "soundtrack-carries-it", "soundtrack-youll-download", "vibes-over-plot", "dreamlike"],
    },
]


class AnimeCard(BaseModel):
    id: UUID
    title: str
    title_english: Optional[str]
    cover_url: Optional[str]
    genres: Optional[list[str]]
    anilist_score: Optional[float]  # AniList's score — not Arcanum community average
    top_tags: list[str]  # Top 3 tag labels from cached_vibe_tags


class VibeCluster(BaseModel):
    id: str
    label: str
    anime: list[AnimeCard]


async def get_anime_for_slugs(
    slugs: list[str],
    limit: int,
    db: AsyncSession,
    slug_to_id: dict,  # Pre-fetched slug → tag_id map. Never query inside this function.
) -> list[AnimeCard]:
    """Returns top N anime that have the most votes across a set of tag slugs.
    slug_to_id must be pre-fetched by the caller — no DB calls for tag IDs here.
    """
    tag_ids = [slug_to_id[s] for s in slugs if s in slug_to_id]
    if not tag_ids:
        return []

    anime_result = await db.execute(
        select(
            Anime,
            func.count(UserAnimeMoodTag.user_id).label("tag_votes")
        )
        .join(UserAnimeMoodTag, UserAnimeMoodTag.anime_id == Anime.id)
        .where(UserAnimeMoodTag.mood_tag_id.in_(tag_ids))
        .group_by(Anime.id)
        .order_by(func.count(UserAnimeMoodTag.user_id).desc())
        .limit(limit)
    )
    rows = anime_result.all()

    # each tuple is (Anime object, vote count).
    cards = []
    for anime, _ in rows:
        # if this anime has any cached vibe tags in its JSONB column
        top_tags = []
        if anime.cached_vibe_tags:
            sorted_tags = sorted(
                anime.cached_vibe_tags.items(),
                key=lambda x: x[1].get("count", 0),
                reverse=True
            )
            # Take the top 3 after sorting, extract just the label strings
            top_tags = [v["label"] for _, v in sorted_tags[:3]]

        # Build a card object with the anime's data plus those top 3 tags, add it to the list.
        # Repeat for every anime in the query results.
        cards.append(AnimeCard(
            id=anime.id,
            title=anime.title,
            title_english=anime.title_english,
            cover_url=anime.cover_url,
            genres=anime.genres,
            anilist_score=anime.average_score,
            top_tags=top_tags,
        ))
    return cards

# TODO: If browse page feels slow with real data, cache entire GET / response with 4hr TTL.
# Response only changes when aggregation job runs — caching is safe and trivial to add.

@router.get("/", response_model=list[VibeCluster])
async def get_vibe_browse(
    db: AsyncSession = Depends(get_db)
):
    """Browse page — returns all clusters with top 5 anime each.
    Bulk-fetches all tag IDs in one query before the cluster loop.
    Only clusters with at least one tagged anime are returned.
    """
    # Single bulk fetch for all tag IDs across all clusters — 1 query of all unique tag slugs across all clusters instead of 8
    # Loops through every cluster, pulls out every slug from every cluster, and deduplicates them.
    all_slugs = list({slug for cluster in VIBE_CLUSTERS for slug in cluster["slugs"]})
    tag_result = await db.execute(
        select(MoodTag.slug, MoodTag.id).where(MoodTag.slug.in_(all_slugs))
    )
    slug_to_id = {slug: tag_id for slug, tag_id in tag_result.all()}

    clusters = []
    # Loop through each predefined cluster. For each one, find the top 5 anime that have votes on any of that cluster's tags.
    # If a cluster has zero tagged anime (nobody's voted), skip it entirely.
    for cluster in VIBE_CLUSTERS:
        anime = await get_anime_for_slugs(
            cluster["slugs"], limit=5, db=db, slug_to_id=slug_to_id
        )
        if anime:
            clusters.append(VibeCluster(
                id=cluster["id"],
                label=cluster["label"],
                anime=anime,
            ))
    return clusters


@router.get("/{slug}", response_model=VibeCluster)
async def get_vibe_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Drill-down — returns all anime for a single tag slug or cluster id."""
    # Check if the incoming slug matches a cluster ID. next() with a generator finds the first match or returns None.
    # I.E. So if someone hits /vibe/late-night, it finds the "Late Night Watch" cluster.
    cluster = next((c for c in VIBE_CLUSTERS if c["id"] == slug), None)

    # If it matched a cluster, use all of that cluster's tag slugs — you'll get anime tagged with any of those 5 tags.
    if cluster:
        slugs = cluster["slugs"]
        label = cluster["label"]
    else:
        tag_result = await db.execute(
            select(MoodTag).where(MoodTag.slug == slug)
        )
        # Not a cluster ID — check if it's a single tag slug (e.g. /vibe/2am-watch)
        tag = tag_result.scalar_one_or_none()
        if not tag:
            # Didn't match a cluster or a tag
            raise HTTPException(status_code=404, detail="Tag or cluster not found")
        # Wrap single slug in a list so get_anime_for_slugs handles it the same as clusters
        slugs = [slug]
        label = tag.label

    # Single tag drill-down still needs its own slug_to_id fetch
    tag_id_result = await db.execute(
        select(MoodTag.slug, MoodTag.id).where(MoodTag.slug.in_(slugs))
    )
    slug_to_id = {s: tid for s, tid in tag_id_result.all()}

    anime = await get_anime_for_slugs(slugs, limit=50, db=db, slug_to_id=slug_to_id)
    return VibeCluster(id=slug, label=label, anime=anime)