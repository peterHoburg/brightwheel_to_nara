"""Pydantic models for Nara Baby Tracker API."""
from datetime import datetime, time
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class NaraActivityType(str, Enum):
    """Types of activities in Nara."""
    DIAPER = "diaper"
    FEEDING = "feeding"
    SLEEP = "sleep"
    MOOD = "mood"
    HEALTH = "health"
    MILESTONE = "milestone"
    MEASUREMENT = "measurement"
    PHOTO = "photo"
    NOTE = "note"
    PUMPING = "pumping"
    BATH = "bath"
    TUMMY_TIME = "tummy_time"
    PLAY = "play"


class FeedingType(str, Enum):
    """Types of feeding."""
    BOTTLE = "bottle"
    BREAST = "breast"
    SOLID = "solid"
    FORMULA = "formula"
    PUMPED = "pumped"


class DiaperStatus(str, Enum):
    """Diaper status types."""
    WET = "wet"
    DIRTY = "dirty"
    BOTH = "both"
    DRY = "dry"


class SleepType(str, Enum):
    """Sleep types."""
    NAP = "nap"
    NIGHT = "night"


# Authentication Models
class NaraLoginRequest(BaseModel):
    """Nara login request."""
    email: str
    password: str


class NaraLoginResponse(BaseModel):
    """Nara login response."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int  # seconds
    user: "NaraUser"


class NaraUser(BaseModel):
    """Nara user model."""
    id: str
    email: str
    name: str
    created_at: datetime
    babies: List["Baby"] = Field(default_factory=list)


# Core Models
class Baby(BaseModel):
    """Baby/Child model in Nara."""
    id: str
    name: str
    birth_date: datetime
    birth_time: Optional[time] = None
    gender: Optional[str] = None
    birth_weight_kg: Optional[float] = None
    birth_height_cm: Optional[float] = None
    photo_url: Optional[str] = None
    parent_ids: List[str] = Field(default_factory=list)
    
    
class Caregiver(BaseModel):
    """Caregiver model."""
    id: str
    name: str
    email: Optional[str] = None
    relationship: str  # mother, father, grandparent, nanny, etc
    baby_ids: List[str] = Field(default_factory=list)


# Activity Models
class NaraBaseActivity(BaseModel):
    """Base activity model for Nara."""
    id: Optional[str] = None
    baby_id: str
    activity_type: NaraActivityType
    timestamp: datetime
    notes: Optional[str] = None
    caregiver_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    

class DiaperRecord(NaraBaseActivity):
    """Diaper change record."""
    activity_type: NaraActivityType = NaraActivityType.DIAPER
    status: DiaperStatus
    color: Optional[str] = None
    consistency: Optional[str] = None
    has_rash: bool = False
    cream_applied: bool = False


class FeedingRecord(NaraBaseActivity):
    """Feeding record."""
    activity_type: NaraActivityType = NaraActivityType.FEEDING
    feeding_type: FeedingType
    amount_ml: Optional[float] = None
    duration_minutes: Optional[int] = None
    left_side_minutes: Optional[int] = None
    right_side_minutes: Optional[int] = None
    food_items: List[str] = Field(default_factory=list)


class SleepRecord(NaraBaseActivity):
    """Sleep record."""
    activity_type: NaraActivityType = NaraActivityType.SLEEP
    sleep_type: SleepType
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    quality: Optional[str] = None  # good, fair, poor
    location: Optional[str] = None  # crib, bed, car, stroller


class HealthRecord(NaraBaseActivity):
    """Health record."""
    activity_type: NaraActivityType = NaraActivityType.HEALTH
    temperature_celsius: Optional[float] = None
    symptoms: List[str] = Field(default_factory=list)
    medications: List[str] = Field(default_factory=list)
    doctor_visit: bool = False


class MeasurementRecord(NaraBaseActivity):
    """Growth measurement record."""
    activity_type: NaraActivityType = NaraActivityType.MEASUREMENT
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    head_circumference_cm: Optional[float] = None


class PhotoRecord(NaraBaseActivity):
    """Photo record."""
    activity_type: NaraActivityType = NaraActivityType.PHOTO
    photo_url: str
    caption: Optional[str] = None
    

class MilestoneRecord(NaraBaseActivity):
    """Milestone record."""
    activity_type: NaraActivityType = NaraActivityType.MILESTONE
    milestone_name: str
    category: str  # motor, cognitive, social, language


class PumpingRecord(NaraBaseActivity):
    """Pumping record."""
    activity_type: NaraActivityType = NaraActivityType.PUMPING
    amount_ml: float
    duration_minutes: Optional[int] = None
    

class TummyTimeRecord(NaraBaseActivity):
    """Tummy time record."""
    activity_type: NaraActivityType = NaraActivityType.TUMMY_TIME
    duration_minutes: int
    

class PlayRecord(NaraBaseActivity):
    """Play activity record."""
    activity_type: NaraActivityType = NaraActivityType.PLAY
    activity_name: str
    duration_minutes: Optional[int] = None
    

# Request/Response Models
class CreateActivityRequest(BaseModel):
    """Request to create an activity."""
    activity: Dict[str, Any]  # Can be any activity type


class CreateActivityResponse(BaseModel):
    """Response after creating an activity."""
    id: str
    success: bool
    activity: Dict[str, Any]


class GetActivitiesRequest(BaseModel):
    """Request to get activities."""
    baby_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    activity_types: Optional[List[NaraActivityType]] = None
    limit: int = 100
    offset: int = 0


class GetActivitiesResponse(BaseModel):
    """Response for getting activities."""
    activities: List[Dict[str, Any]]
    total_count: int
    has_more: bool
    

class BabyStatistics(BaseModel):
    """Statistics for a baby."""
    baby_id: str
    date: datetime
    total_feeds: int
    total_diapers: int
    total_sleep_hours: float
    last_feed_time: Optional[datetime] = None
    last_diaper_time: Optional[datetime] = None
    last_sleep_time: Optional[datetime] = None
    

# Update forward references
NaraLoginResponse.model_rebuild()
NaraUser.model_rebuild()