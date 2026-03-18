from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import UserAnimeRelationship, Anime, WatchStatus
from app.routers.anime_list import get_current_user_id
from uuid import UUID
from datetime import datetime
from defusedxml.ElementTree import fromstring
import httpx
from pydantic import BaseModel

router = APIRouter(prefix="/import", tags=["import"])

MAL_STATUS_MAP = {
    "Completed": WatchStatus.completed,
    "Watching": WatchStatus.watching,
    "Plan to Watch": WatchStatus.plan_to_watch,
    "Dropped": WatchStatus.dropped,
    "On-Hold": WatchStatus.on_hold,
}

ANILIST_STATUS_MAP = {
    "COMPLETED": WatchStatus.completed,
    "CURRENT": WatchStatus.watching,
    "PLANNING": WatchStatus.plan_to_watch,
    "DROPPED": WatchStatus.dropped,
    "PAUSED": WatchStatus.on_hold,
    "REPEATING": WatchStatus.watching,
}

ANILIST_QUERY = """
query ($username: String, $page: Int) {
  MediaListCollection(userName: $username, type: ANIME, chunk: $page, perChunk: 500) {
    lists {
      entries {
        mediaId
        status
        score(format: POINT_10)
        progress
        startedAt { year month day }
        completedAt { year month day }
        repeat
        media {
          title { romaji }
        }
      }
    }
    hasNextChunk
  }
}
"""

class AniListImportRequest(BaseModel):
    username: str

def parse_anilist_date(date_obj: dict | None) -> datetime | None:
    """Parse AniList date object {year, month, day} into datetime."""
    if not date_obj or not date_obj.get("year"):
        return None
    try:
        return datetime(date_obj["year"], date_obj["month"] or 1, date_obj["day"] or 1)
    except (ValueError, TypeError):
        return None
    
def parse_date(date_str: str):
    """Returns None if date is 0000-00-00 or invalid."""
    if not date_str or date_str == "0000-00-00":
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None

def parse_mal_xml(content: bytes) -> list[dict]:
    """Parse MAL XML export. Uses defusedxml to prevent entity expansion attacks."""
    root = fromstring(content)

    # Sanity check — verify this is actually a MAL export
    if root.tag != "myanimelist" or not root.findall("anime"):
        raise ValueError("This doesn't appear to be a MAL export file")

    entries = []
    for anime in root.findall("anime"):
        def get(tag):
            el = anime.find(tag)
            return el.text.strip() if el is not None and el.text else None

        mal_id = get("series_animedb_id")
        status = get("my_status")
        score = get("my_score")
        watched_eps = get("my_watched_episodes")
        rewatch_count = get("my_times_watched")
        title = get("series_title")

        if not mal_id or not status:
            continue

        entries.append({
            "mal_id": int(mal_id),
            "title": title,
            "status": MAL_STATUS_MAP.get(status),
            "score": int(score) if score and score != "0" else None,
            "watched_eps": int(watched_eps) if watched_eps else None,
            "start_date": parse_date(get("my_start_date")),
            "finish_date": parse_date(get("my_finish_date")),
            "rewatch_count": int(rewatch_count) if rewatch_count else 0,
        })
    return entries

@router.post("/mal", status_code=200)
async def import_mal(
    file: UploadFile = File(...),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Import a MAL XML export into the user's list.
    
    Uses two bulk queries instead of per-entry queries — O(2) DB calls regardless
    of list size.
    """
    if not file.filename.endswith(".xml"):
        raise HTTPException(status_code=400, detail="File must be a .xml MAL export")

    content = await file.read()

    try:
        entries = parse_mal_xml(content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not entries:
        raise HTTPException(status_code=400, detail="No anime entries found in file")

    # --- Bulk fetch 1: all anime matching MAL IDs in the file ---
    mal_ids = [e["mal_id"] for e in entries]
    anime_result = await db.execute(
        select(Anime).where(Anime.mal_id.in_(mal_ids))
    )
    anime_by_mal_id = {a.mal_id: a for a in anime_result.scalars().all()}

    # --- Bulk fetch 2: all anime already in this user's list ---
    existing_result = await db.execute(
        select(UserAnimeRelationship.anime_id).where(
            UserAnimeRelationship.user_id == user_id
        )
    )
    existing_anime_ids = set(existing_result.scalars().all())

    # --- Pure Python loop — no DB calls inside ---
    imported = 0
    skipped = 0
    unmatched = []

    for entry in entries:
        if entry["status"] is None:
            continue

        anime = anime_by_mal_id.get(entry["mal_id"])
        if not anime:
            unmatched.append(entry["title"])
            continue

        if anime.id in existing_anime_ids:
            skipped += 1
            continue

        relationship = UserAnimeRelationship(
            user_id=user_id,
            anime_id=anime.id,
            status=entry["status"],
            currently_watching_ep=entry["watched_eps"],
            date_started=entry["start_date"],
            date_completed=entry["finish_date"],
            # TODO: add score_source enum (multi_axis, imported_mal, imported_anilist)
            # so stats page can distinguish real multi-axis scores from imported single scores
            computed_overall=entry["score"],
            rewatch_count=entry["rewatch_count"] or 0,
        )
        db.add(relationship)
        imported += 1

    await db.commit()

    return {
        "imported": imported,
        "skipped": skipped,
        "unmatched_count": len(unmatched),
        "unmatched_titles": unmatched[:20],
        "total_in_file": len(entries)
    }

    # --- Fetch all entries from AniList GraphQL API ---
    # Uses pagination (chunks of 500) to handle large lists.
    # AniList IDs match our anilist_id column directly — no ID mapping needed.
    # Unlike MAL import, no file parsing required — API returns structured JSON.

@router.post("/anilist", status_code=200)
async def import_anilist(
    body: AniListImportRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Import anime list directly from AniList using username.
    No file upload needed — queries AniList GraphQL API directly.
    Uses anilist_id for matching — direct lookup, no ID mapping needed.
    """
    entries = []
    page = 1

    async with httpx.AsyncClient() as client:
        while True:
            try:
                res = await client.post(
                    "https://graphql.anilist.co",
                    json={
                        "query": ANILIST_QUERY,
                        "variables": {"username": body.username, "page": page}
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )
                res.raise_for_status()
            except httpx.HTTPError:
                raise HTTPException(status_code=502, detail="Could not reach AniList. Try again.")

            data = res.json()

            if "errors" in data:
                raise HTTPException(status_code=404, detail=f"AniList user '{body.username}' not found.")

            collection = data["data"]["MediaListCollection"]
            for lst in collection["lists"]:
                for entry in lst["entries"]:
                    status = ANILIST_STATUS_MAP.get(entry["status"])
                    if not status:
                        continue
                    score = entry.get("score")
                    entries.append({
                        "anilist_id": entry["mediaId"],
                        "title": entry["media"]["title"]["romaji"],
                        "status": status,
                        "score": int(score) if score and score > 0 else None,
                        "watched_eps": entry.get("progress"),
                        "start_date": parse_anilist_date(entry.get("startedAt")),
                        "finish_date": parse_anilist_date(entry.get("completedAt")),
                        "rewatch_count": entry.get("repeat") or 0,
                    })

            if not collection["hasNextChunk"]:
                break
            page += 1

    if not entries:
        raise HTTPException(status_code=400, detail="No anime entries found for this AniList user.")

    #--- Bulk fetch 1: match AniList IDs to our anime table ---
    # Direct anilist_id lookup — O(1) per entry, no fuzzy matching.

    anilist_ids = [e["anilist_id"] for e in entries]
    anime_result = await db.execute(
        select(Anime).where(Anime.anilist_id.in_(anilist_ids))
    )
    anime_by_anilist_id = {a.anilist_id: a for a in anime_result.scalars().all()}

    # Bulk fetch 2: existing user list
    # Prevents duplicates — same pattern as MAL import.
    existing_result = await db.execute(
        select(UserAnimeRelationship.anime_id).where(
            UserAnimeRelationship.user_id == user_id
        )
    )
    existing_anime_ids = set(existing_result.scalars().all())

    # Pure Python loop — no DB calls inside
    # Same bulk-fetch-then-loop pattern established in MAL import.
    imported = 0
    skipped = 0
    unmatched = []

    for entry in entries:
        anime = anime_by_anilist_id.get(entry["anilist_id"])
        if not anime:
            unmatched.append(entry["title"])
            continue

        if anime.id in existing_anime_ids:
            skipped += 1
            continue

        relationship = UserAnimeRelationship(
            user_id=user_id,
            anime_id=anime.id,
            status=entry["status"],
            currently_watching_ep=entry["watched_eps"],
            date_started=entry["start_date"],
            date_completed=entry["finish_date"],
            # TODO: add score_source enum (multi_axis, imported_mal, imported_anilist)
            computed_overall=entry["score"],
            rewatch_count=entry["rewatch_count"] or 0,
        )
        db.add(relationship)
        imported += 1

    await db.commit()

    return {
        "imported": imported,
        "skipped": skipped,
        "unmatched_count": len(unmatched),
        "unmatched_titles": unmatched[:20],
        "total_in_file": len(entries)
    }