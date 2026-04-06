from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float, Text, ForeignKey, Enum as SQLAlchemyEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.database import Base
import uuid
from datetime import datetime, timezone
import enum
from pgvector.sqlalchemy import Vector

# NOTE: This file uses the legacy Column() style throughout.
# TODO: Migrate to SQLAlchemy 2.0 Mapped[] style in a future refactor session.

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    # taste_vector: 128-dim taste fingerprint.
    # Segments: 18 genre dims (weight 0.40) + 5 score axis dims (weight 0.20) + 65 mood tag dims (weight 0.40) + 40 buffer zeros
    # NULL for users with <5 scored anime — vector meaningless below this threshold.
    # Recomputed every 24hrs by APScheduler. Phase 3.4 uses <=> cosine distance for compatibility.
    taste_vector = Column(Vector(128), nullable=True)
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
    __table_args__ = (UniqueConstraint('user_id', 'anime_id'),)

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
    computed_overall = Column(Float, nullable=True)

    # Rewatch
    rewatch_count = Column(Integer, default=0)
    rewatch_score = Column(Integer, nullable=True)

    # Progress
    currently_watching_ep = Column(Integer, nullable=True)
    date_started = Column(DateTime(timezone=True), nullable=True)
    date_completed = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class MoodTag(Base):
    __tablename__ = "mood_tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # 100 chars is fine for curated vocabulary. If community proposals open up, revisit.
    label = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    # usage_count is maintained by pg_cron aggregation job. Do NOT increment in application code.
    # Incrementing here would create race conditions under concurrent writes.
    usage_count = Column(Integer, default=0)
    is_approved = Column(Boolean, default=True)
    # is_suggested: currently unused (all tags are hand-curated, defaults to False).
    # Reserved for future community proposal system — user-proposed tags start as
    # is_suggested=True until reviewed and approved by moderators.
    is_suggested = Column(Boolean, default=False)
    # Silent self-referential FK for chart rollup aggregation only.
    # Never exposed during tagging. I.E. 'melancholy' rolls up to 'Emotional' parent.
    parent_mood_id = Column(UUID(as_uuid=True), ForeignKey("mood_tags.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class UserAnimeMoodTag(Base):
    __tablename__ = "user_anime_mood_tags"

    # Intentionally separate FKs to users and anime instead of to user_anime_relationships.
    # A user can tag an anime without it being on their list. Keeps flywheel frictionless.
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    anime_id = Column(UUID(as_uuid=True), ForeignKey("anime.id", ondelete="CASCADE"), primary_key=True, index=True)
    mood_tag_id = Column(UUID(as_uuid=True), ForeignKey("mood_tags.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Follow(Base):
    __tablename__ = "follows"

    # Simple social graph — no approval flow, just follow/unfollow.
    # Follows = Circle
    # follower_id follows following_id.
    # Composite PK enforces uniqueness — no separate UniqueConstraint needed.
    # Phase 4+: add weight column for "power follow" multiplier on taste scores.
    follower_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    following_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))