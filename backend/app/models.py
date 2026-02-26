from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.database import Base
import uuid
from datetime import datetime, timezone

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