from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models import WatchStatus

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    avatar_url: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None

# --- List Management Schemas ---

class ListEntryCreate(BaseModel):
    """Minimum required: anime_id + status. Everything else is optional."""
    anime_id: UUID
    status: WatchStatus
    # Progress
    currently_watching_ep: Optional[int] = None
    date_started: Optional[datetime] = None
    date_completed: Optional[datetime] = None
    # Multi-axis scoring — opt-in power user layer
    score_story: Optional[int] = None
    score_art: Optional[int] = None
    score_sound: Optional[int] = None
    score_characters: Optional[int] = None
    score_enjoyment: Optional[int] = None
    # Rewatch
    rewatch_count: Optional[int] = 0
    rewatch_score: Optional[int] = None

    @field_validator(
        'score_story', 'score_art', 'score_sound',
        'score_characters', 'score_enjoyment', 'rewatch_score',
        mode='before'
    )
    @classmethod
    def validate_score_range(cls, v):
        """Scores must be between 1-10. Null is allowed (score not yet given)."""
        if v is not None and not (1 <= v <= 10):
            raise ValueError("Score must be between 1 and 10")
        return v

class ListEntryUpdate(BaseModel):
    """All fields optional — user can update any subset."""
    status: Optional[WatchStatus] = None
    currently_watching_ep: Optional[int] = None
    date_started: Optional[datetime] = None
    date_completed: Optional[datetime] = None
    score_story: Optional[int] = None
    score_art: Optional[int] = None
    score_sound: Optional[int] = None
    score_characters: Optional[int] = None
    score_enjoyment: Optional[int] = None
    rewatch_count: Optional[int] = None
    rewatch_score: Optional[int] = None

    @field_validator(
        'score_story', 'score_art', 'score_sound',
        'score_characters', 'score_enjoyment', 'rewatch_score',
        mode='before'
    )
    @classmethod
    def validate_score_range(cls, v):
        """Scores must be between 1-10. Null is allowed (score not yet given)."""
        if v is not None and not (1 <= v <= 10):
            raise ValueError("Score must be between 1 and 10")
        return v

class ListEntryResponse(BaseModel):
    """Full entry returned to client."""
    id: UUID
    user_id: UUID
    anime_id: UUID
    status: WatchStatus
    currently_watching_ep: Optional[int]
    date_started: Optional[datetime]
    date_completed: Optional[datetime]
    score_story: Optional[int]
    score_art: Optional[int]
    score_sound: Optional[int]
    score_characters: Optional[int]
    score_enjoyment: Optional[int]
    computed_overall: Optional[int]
    rewatch_count: int
    rewatch_score: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}