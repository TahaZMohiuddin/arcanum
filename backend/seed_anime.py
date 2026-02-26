import asyncio
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from app.models import Anime

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

ANILIST_QUERY = """
query ($page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    pageInfo {
      hasNextPage
    }
    media(type: ANIME, sort: POPULARITY_DESC) {
      id
      title {
        romaji
        english
      }
      description(asHtml: false)
      coverImage {
        large
      }
      genres
      episodes
      averageScore
      season
      seasonYear
    }
  }
}
"""

async def fetch_page(client: httpx.AsyncClient, page: int):
    response = await client.post(
        "https://graphql.anilist.co",
        json={
            "query": ANILIST_QUERY,
            "variables": {"page": page, "perPage": 50}
        },
        headers={"Content-Type": "application/json"}
    )
    return response.json()

async def seed():
    print("Starting AniList seed...")
    total = 0

    async with AsyncSessionLocal() as db:
        async with httpx.AsyncClient() as client:
            for page in range(1, 11):  # 10 pages x 50 = 500 anime
                print(f"Fetching page {page}/10...")
                data = await fetch_page(client, page)

                if "errors" in data:
                    print(f"API error: {data['errors']}")
                    break

                media_list = data["data"]["Page"]["media"]
                has_next = data["data"]["Page"]["pageInfo"]["hasNextPage"]

                for media in media_list:
                    # Skip if already exists
                    result = await db.execute(
                        select(Anime).where(Anime.anilist_id == media["id"])
                    )
                    if result.scalar_one_or_none():
                        continue

                    anime = Anime(
                        anilist_id=media["id"],
                        title=media["title"]["romaji"],
                        title_english=media["title"].get("english"),
                        synopsis=media.get("description"),
                        cover_url=media["coverImage"]["large"] if media.get("coverImage") else None,
                        genres=media.get("genres", []),
                        episode_count=media.get("episodes"),
                        average_score=media.get("averageScore"),
                        season=media.get("season"),
                        season_year=media.get("seasonYear"),
                        cached_vibe_tags={}
                    )
                    db.add(anime)
                    total += 1

                await db.commit()
                print(f"Page {page} done. Total seeded so far: {total}")

                if not has_next:
                    break

                await asyncio.sleep(0.5)  # Be nice to AniList-senpai's API. Onegaishimasu!

    print(f"Seed complete. {total} anime added to database.")

if __name__ == "__main__":
    asyncio.run(seed())