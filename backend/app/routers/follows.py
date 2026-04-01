from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import Follow, User
from app.routers.anime_list import get_current_user_id
from uuid import UUID
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/users", tags=["follows"])


class FollowStats(BaseModel):
    circle_count: int      # people you follow
    circled_by_count: int  # people who follow you

class UserSummary(BaseModel):
    username: str
    avatar_url: Optional[str]
    model_config = {"from_attributes": True}

async def get_user_by_username(username: str, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/{username}/follow", status_code=201)
async def follow_user(
    username: str,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Add a user to your circle. Frontend label: 'Add to Circle'"""
    # Get target user
    user = await get_user_by_username(username, db)

    # Prevent self-follow
    if user.id == current_user_id:
        raise HTTPException(status_code=400, detail="You cannot add yourself to your circle")

    # Check if already following
    existing = await db.execute(
        select(Follow).where(
            Follow.follower_id == current_user_id,
            Follow.following_id == user.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already in your circle")

    follow = Follow(follower_id=current_user_id, following_id=user.id)
    db.add(follow)
    await db.commit()
    return {"message": f"{username} added to your circle"}


@router.delete("/{username}/follow", status_code=204)
async def unfollow_user(
    username: str,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Remove a user from your circle. Frontend label: 'Remove from Circle'"""
    user = await get_user_by_username(username, db)

    follow_result = await db.execute(
        select(Follow).where(
            Follow.follower_id == current_user_id,
            Follow.following_id == user.id
        )
    )
    follow = follow_result.scalar_one_or_none()
    if not follow:
        raise HTTPException(status_code=404, detail="Not in your circle")

    await db.delete(follow)
    await db.commit()


@router.get("/{username}/circle", response_model=FollowStats)
async def get_circle_stats(
    username: str,
    db: AsyncSession = Depends(get_db)
):
    """Returns circle counts for a user profile.
    circle_count = people they follow (their circle)
    circled_by_count = people who follow them (circled by)
    """
    user = await get_user_by_username(username, db)

    circle_count = await db.execute(
        select(func.count()).where(Follow.follower_id == user.id)
    )
    circled_by_count = await db.execute(
        select(func.count()).where(Follow.following_id == user.id)
    )

    return FollowStats(
        circle_count=circle_count.scalar(),
        circled_by_count=circled_by_count.scalar()
    )


@router.get("/{username}/circle/following", response_model=list[UserSummary])
async def get_following(
    username: str,
    db: AsyncSession = Depends(get_db)
):
    """List of users in this user's circle (people they follow)."""
    user = await get_user_by_username(username, db)

    following_result = await db.execute(
        select(User)
        .join(Follow, Follow.following_id == User.id)
        .where(Follow.follower_id == user.id)
        .order_by(Follow.created_at.desc())
    )
    return following_result.scalars().all()


@router.get("/{username}/circle/followers", response_model=list[UserSummary])
async def get_followers(
    username: str,
    db: AsyncSession = Depends(get_db)
):
    """List of users who have this user in their circle (people who follow them)."""
    user = await get_user_by_username(username, db)

    followers_result = await db.execute(
        select(User)
        .join(Follow, Follow.follower_id == User.id)
        .where(Follow.following_id == user.id)
        .order_by(Follow.created_at.desc())
    )
    return followers_result.scalars().all()