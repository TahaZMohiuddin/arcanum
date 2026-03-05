from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.database import AsyncSessionLocal
from app.models import MoodTag, UserAnimeMoodTag, Anime
from collections import defaultdict
import logging

# TODO: Consider migrating to Supabase pg_cron in production if APScheduler becomes a bottleneck
# TODO: Add presence TTL cleanup job here in Phase 4 (purge presence records older than 30 min)
# TODO Phase 4 — Add presence TTL cleanup job here.
# The presence table tracks "watching right now" state (user_id, anime_id, episode, updated_at).
# Without cleanup, presence records for users who closed the tab accumulate as ghost viewers.
# Fix: scheduled job deletes records where updated_at < now() - interval '30 minutes'.
# Frontend pings /presence every ~2 min while watching to keep the record fresh.
# When pings stop, updated_at goes stale and this job cleans it up.
# SQL: DELETE FROM presence WHERE updated_at < now() - interval '30 minutes'

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def aggregate_vibe_tags():
    """Runs every 4 hours.
    1. Single bulk query aggregates tag vote counts across all anime at once
    2. Groups results in Python by anime_id
    3. Batch updates cached_vibe_tags JSONB on anime table
    4. Batch updates usage_count on mood_tags table

    usage_count is maintained here — never increment it in application code.
    """
    logger.info("Starting vibe tag aggregation...")
    async with AsyncSessionLocal() as db:

        # Single query — all tag counts across all anime at once. No N+1.
        all_counts_result = await db.execute(
            select(
                UserAnimeMoodTag.anime_id,
                MoodTag.id,
                MoodTag.slug,
                MoodTag.label,
                func.count(UserAnimeMoodTag.user_id).label("count")
            )
            .join(MoodTag, UserAnimeMoodTag.mood_tag_id == MoodTag.id)
            .group_by(UserAnimeMoodTag.anime_id, MoodTag.id, MoodTag.slug, MoodTag.label)
            .order_by(UserAnimeMoodTag.anime_id, func.count(UserAnimeMoodTag.user_id).desc())
        )
        rows = all_counts_result.all()

        # Group in Python by anime_id
        anime_tag_map = defaultdict(dict)
        tag_usage = defaultdict(int)

        for anime_id, tag_id, slug, label, count in rows:
            anime_tag_map[anime_id][slug] = {"label": label, "count": count}
            tag_usage[tag_id] += count

        # Update cached_vibe_tags per anime — one UPDATE per anime, unavoidable
        for anime_id, cached in anime_tag_map.items():
            await db.execute(
                update(Anime)
                .where(Anime.id == anime_id)
                .values(cached_vibe_tags=cached)
            )

        # Update usage_count per tag
        for tag_id, total in tag_usage.items():
            await db.execute(
                update(MoodTag)
                .where(MoodTag.id == tag_id)
                .values(usage_count=total)
            )

        await db.commit()
    logger.info(f"Vibe tag aggregation complete. {len(anime_tag_map)} anime updated.")


def start_scheduler():
    scheduler.add_job(
        aggregate_vibe_tags,
        trigger="interval",
        hours=4,
        id="aggregate_vibe_tags",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started. Vibe tag aggregation runs every 4 hours.")