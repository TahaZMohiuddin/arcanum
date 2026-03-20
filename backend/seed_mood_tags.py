import asyncio
import re
from sqlalchemy import select
from app.models import MoodTag
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from app.database import AsyncSessionLocal

def make_slug(label: str) -> str:
    """Convert label to URL-safe slug. '2am watch' → '2am-watch'"""
    slug = label.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")

MOOD_TAGS = [
    # Vibe (18)
    "2am watch",
    "emotionally devastating",
    "wholesome",
    "melancholy",
    "hopeful",
    "unsettling",
    "peaceful",
    "bittersweet",
    "haunting",
    "uplifting",
    "bizarre",
    "cozy",
    "dreamlike",
    "nostalgic",
    "lonely",
    "existential dread",
    "makes you stare at the ceiling",
    "chaotic energy",
    # Occasion (12)
    "watch with friends",
    "solo experience",
    "good cry",
    "background watch",
    "binge worthy",
    "slow burn",
    "gateway anime",
    "comfort rewatch",
    "palate cleanser",
    "sick day watch",
    "hype watch",
    "rewatch every year",
    # Quality (13)
    "peak fiction",
    "hidden gem",
    "so bad its good",
    "overhyped",
    "underrated",
    "certified classic",
    "rewarding payoff",
    "sticks the landing",
    "better than its reputation",
    "adaptation did it justice",
    "ahead of its time",
    "aged like wine",
    "guilty pleasure",
    # Style (14)
    "visually stunning",
    "soundtrack carries it",
    "found family",
    "character driven",
    "you'll ugly cry",
    "emotional gut punch finale",
    "comfort food anime",
    "grows on you",
    "vibes over plot",
    "style over substance",
    "slow start worth it",
    "anxiety inducing",
    "quietly devastating",
    "nerve-wracking",
    "atmospheric",
    # New
    "banger OP/ED",
    "philosophical",
    "damn good villain",
    "I'm not okay rn",
    "epic scope",
    "cozy but dark",
    "died from laughter",
    "turn your brain off",
]

async def seed():
    print("Seeding mood tags...")
    async with AsyncSessionLocal() as db:
        # Bulk fetch existing slugs in one query. Same consistent pattern as MAL import tool!
        result = await db.execute(select(MoodTag.slug))
        existing_slugs = set(result.scalars().all())

        added = 0
        skipped = 0
        for label in MOOD_TAGS:
            slug = make_slug(label)
            if slug in existing_slugs:
                skipped += 1
                continue
            tag = MoodTag(
                label=label,
                slug=slug,
                is_approved=True,
                is_suggested=False,
                usage_count=0,
            )
            db.add(tag)
            added += 1
        await db.commit()
    print(f"Done. {added} tags added, {skipped} skipped (already existed).")

if __name__ == "__main__":
    asyncio.run(seed())