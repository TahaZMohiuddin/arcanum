import asyncio
import json
import os
import httpx
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import AsyncSessionLocal
from app.models import Anime, MoodTag, UserAnimeMoodTag
from uuid import UUID
import logging
from dotenv import load_dotenv
from app.constants import SYSTEM_USER_ID

load_dotenv()

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MIN_CONFIRMED_TAGS = 3  # Skip anime that already have 3+ confirmed community tags
MAX_ANIME_PER_RUN = 150 # Process top 150 by popularity per run
COMMIT_BATCH_SIZE = 25  # Commit every N anime to avoid 150 individual commits


async def get_all_tag_labels(db: AsyncSession) -> list[str]:
    """Fetch all approved tag labels in one query."""
    result = await db.execute(
        select(MoodTag.label).where(MoodTag.is_approved == True)
    )
    return result.scalars().all()

async def get_anime_needing_suggestions(db: AsyncSession) -> list[Anime]:
    """Fetch anime with fewer than MIN_CONFIRMED_TAGS real community votes
    AND no existing system user tags.
    Excludes anime already tagged by system user — prevents re-processing same anime every run.
    Ordered by average_score desc — suggest for popular anime first.
    """
    # Subquery: real community vote counts (excludes system user)
    confirmed_counts = (
        select(
            UserAnimeMoodTag.anime_id,
            func.count(UserAnimeMoodTag.user_id).label("vote_count")
        )
        .where(UserAnimeMoodTag.user_id != SYSTEM_USER_ID)
        .group_by(UserAnimeMoodTag.anime_id)
        .subquery()
    )

    # Subquery: anime already tagged by system user
    system_tagged = (
        select(UserAnimeMoodTag.anime_id)
        .where(UserAnimeMoodTag.user_id == SYSTEM_USER_ID)
        .distinct()
        .subquery()
    )

    result = await db.execute(
        select(Anime)
        .outerjoin(confirmed_counts, confirmed_counts.c.anime_id == Anime.id)
        .outerjoin(system_tagged, system_tagged.c.anime_id == Anime.id)
        .where(
            ((confirmed_counts.c.vote_count < MIN_CONFIRMED_TAGS) |
             (confirmed_counts.c.vote_count == None)) &
            (system_tagged.c.anime_id == None)  # Not yet tagged by system
        )
        .order_by(Anime.average_score.desc().nullslast())
        .limit(MAX_ANIME_PER_RUN)
    )
    return result.scalars().all()


async def suggest_tags_for_anime(
    anime: Anime,
    all_tags: list[str],
    client: httpx.AsyncClient,
    max_retries: int = 2
) -> list[str]:
    """Call Claude API to suggest tags for a single anime.
    Returns list of tag labels from the approved vocabulary only.
    LLM picks from existing tags — it does not create new ones.
    Retries up to max_retries times with exponential backoff on network failure.
    """
    tag_list = "\n".join(f"- {tag}" for tag in all_tags)
    prompt = f"""You are tagging anime for a community database. Given this anime's details, select which tags from the approved list apply. Return ONLY a JSON array of tag labels. No explanation, no new tags — only pick from the list.

Anime: {anime.title}
{f'English title: {anime.title_english}' if anime.title_english else ''}
Genres: {', '.join(anime.genres) if anime.genres else 'Unknown'}
Synopsis: {(anime.synopsis or '')[:500]}

Approved tags (pick only from these):
{tag_list}

Return format: ["tag one", "tag two", "tag three"]
Return between 2 and 6 tags. Only return the JSON array."""
    
    # try up to 3 times total (1 initial + 2 retries) before giving up
    for attempt in range(max_retries + 1):
        try:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 200,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30.0
            )
            response.raise_for_status()
            break  # Success — exit retry loop
        except (httpx.HTTPError, httpx.ReadError) as e:
            if attempt == max_retries:
                logger.warning(f"API call failed for {anime.title} after {max_retries + 1} attempts: {e}")
                return []
            wait = 2 ** attempt  # 1s, then 2s
            logger.warning(f"API call failed for {anime.title} (attempt {attempt + 1}), retrying in {wait}s: {e}")
            await asyncio.sleep(wait)

    # Parse response — separate try/except from network errors
    try:
        data = response.json()
        raw = data["content"][0]["text"].strip()
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Invalid JSON response for {anime.title}: {e}")
        return []

    # Parse LLM output — handles backtick wrapping and thinking out loud
    try:
        # Strip markdown code fences if LLM wraps response
        clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        match = re.search(r'\[.*?\]', clean, re.DOTALL)
        if match:
            suggested = json.loads(match.group())
        else:
            suggested = json.loads(clean)
        approved_set = set(all_tags)
        return [tag for tag in suggested if tag in approved_set]
    except (json.JSONDecodeError, KeyError):
        logger.warning(f"Failed to parse LLM response for {anime.title}: {raw}")
        return []


async def run_llm_suggest():
    """Main job. Fetches anime needing tags, calls Claude for suggestions,
    inserts results as system user votes.

    The system user ID on UserAnimeMoodTag is the signal for LLM-suggested votes.
    We do NOT modify MoodTag.is_suggested — that flag means "LLM-created tag",
    not "LLM-suggested application". All 65 tags are hand-curated.

    Commits in batches of COMMIT_BATCH_SIZE to avoid 150 individual commits.
    """
    logger.info("Starting LLM tag suggestion job...")
    async with AsyncSessionLocal() as db:
        all_tags = await get_all_tag_labels(db)
        anime_list = await get_anime_needing_suggestions(db)
        logger.info(f"Processing {len(anime_list)} anime...")

        # Bulk fetch existing system suggestions — explicit tuple cast for safety
        existing_result = await db.execute(
            select(UserAnimeMoodTag.anime_id, UserAnimeMoodTag.mood_tag_id)
            .where(UserAnimeMoodTag.user_id == SYSTEM_USER_ID)
        )
        existing_suggestions = {(row.anime_id, row.mood_tag_id) for row in existing_result.all()}

        # Bulk fetch tag label → id map
        tag_meta_result = await db.execute(
            select(MoodTag.label, MoodTag.id)
            .where(MoodTag.is_approved == True)
        )
        tag_meta = {label: tag_id for label, tag_id in tag_meta_result.all()}

        added = 0
        async with httpx.AsyncClient() as client:
            for i, anime in enumerate(anime_list):
                suggested_labels = await suggest_tags_for_anime(anime, all_tags, client)

                for label in suggested_labels:
                    if label not in tag_meta:
                        continue
                    tag_id = tag_meta[label]

                    if (anime.id, tag_id) in existing_suggestions:
                        continue

                    vote = UserAnimeMoodTag(
                        user_id=SYSTEM_USER_ID,
                        anime_id=anime.id,
                        mood_tag_id=tag_id,
                    )
                    db.add(vote)
                    existing_suggestions.add((anime.id, tag_id))
                    added += 1

                # Batch commit every COMMIT_BATCH_SIZE anime
                if (i + 1) % COMMIT_BATCH_SIZE == 0:
                    await db.commit()
                    logger.info(f"Committed batch at anime {i + 1}/{len(anime_list)}")

                await asyncio.sleep(0.5)

        # Final commit for remainder
        await db.commit()
        logger.info(f"LLM suggestion job complete. {added} suggestions added.")


if __name__ == "__main__":
    asyncio.run(run_llm_suggest())