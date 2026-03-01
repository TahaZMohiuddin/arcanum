from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.database import Base
import uuid
from datetime import datetime, timezone
import enum

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Anime(Base):
    __tablename__ = "anime"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    anilist_id = Column(Integer, unique=True, nullable=False, index=True)
    mal_id = Column(Integer, nullable=True, index=True)
    title = Column(String(500), nullable=False)
    title_english = Column(String(500), nullable=True)
    synopsis = Column(Text, nullable=True)
    cover_url = Column(String(500), nullable=True)
    genres = Column(ARRAY(String), nullable=True)
    episode_count = Column(Integer, nullable=True)
    cached_vibe_tags = Column(JSONB, default=dict)
    average_score = Column(Integer, nullable=True)
    season = Column(String(50), nullable=True)
    season_year = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class WatchStatus(enum.Enum):
    watching = "watching"
    completed = "completed"
    dropped = "dropped"
    plan_to_watch = "plan_to_watch"
    on_hold = "on_hold"

class UserAnimeRelationship(Base):
    __tablename__ = "user_anime_relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    anime_id = Column(UUID(as_uuid=True), ForeignKey("anime.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(SQLAlchemyEnum(WatchStatus), nullable=False)
    
    # Status is the only required field.
    # Optional Mood Tags live in user_anime_mood_tags
    # Multi-axis scoring — all nullable. User can score none, some, or all.
    # computed_overall = average of whichever axes are filled in.
    # Feeds taste_vector computation for social matching.
    # REWATCH fields only surface in UI when rewatch_count > 0.

    score_story = Column(Integer, nullable=True)
    score_art = Column(Integer, nullable=True)
    score_sound = Column(Integer, nullable=True)
    score_characters = Column(Integer, nullable=True)
    score_enjoyment = Column(Integer, nullable=True)
    computed_overall = Column(Integer, nullable=True)

    # Rewatch
    rewatch_count = Column(Integer, default=0)
    rewatch_score = Column(Integer, nullable=True)

    # Progress
    currently_watching_ep = Column(Integer, nullable=True)
    date_started = Column(DateTime(timezone=True), nullable=True)
    date_completed = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))