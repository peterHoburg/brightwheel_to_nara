"""Pydantic models for Brightwheel API."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class ActivityType(str, Enum):
    """Types of activities in Brightwheel."""
    DIAPER = "diaper"
    BOTTLE = "bottle"
    FOOD = "food"
    NAP = "nap"
    MOOD = "mood"
    TEMPERATURE = "temperature"
    INCIDENT = "incident"
    MEDICATION = "medication"
    PHOTO = "photo"
    NOTE = "note"
    POTTY = "potty"
    

class DiaperType(str, Enum):
    """Types of diaper changes."""
    WET = "wet"
    BM = "bm"
    WET_BM = "wet_bm"
    DRY = "dry"


class MoodType(str, Enum):
    """Mood types."""
    HAPPY = "happy"
    SAD = "sad"
    TIRED = "tired"
    FUSSY = "fussy"
    CALM = "calm"


# Authentication Models
class LoginRequest(BaseModel):
    """Login request model."""
    username: str = Field(..., description="Email or phone number")
    password: str
    remember_me: bool = True


class LoginResponse(BaseModel):
    """Login response model."""
    session_token: str
    user_id: str
    user_type: str
    school_id: Optional[str] = None
    expires_at: datetime


class Session(BaseModel):
    """Session information."""
    token: str
    cookies: Dict[str, str]
    expires_at: datetime
    user_id: str


# Core Models
class Guardian(BaseModel):
    """Guardian/Parent model."""
    id: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    relationship: Optional[str] = None
    student_ids: List[str] = Field(default_factory=list)
    profile_photo_url: Optional[str] = None


class Room(BaseModel):
    """Classroom/Room model."""
    id: str
    name: str
    school_id: str
    teacher_ids: List[str] = Field(default_factory=list)
    student_ids: List[str] = Field(default_factory=list)
    age_range: Optional[str] = None


class Student(BaseModel):
    """Student/Child model."""
    id: str
    first_name: str
    last_name: str
    birthdate: datetime
    room_id: Optional[str] = None
    room_name: Optional[str] = None
    guardian_ids: List[str] = Field(default_factory=list)
    profile_photo_url: Optional[str] = None
    allergies: List[str] = Field(default_factory=list)
    medical_notes: Optional[str] = None
    enrollment_status: str = "active"


class Teacher(BaseModel):
    """Teacher/Staff model."""
    id: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    room_ids: List[str] = Field(default_factory=list)
    profile_photo_url: Optional[str] = None


# Activity Models
class BaseActivity(BaseModel):
    """Base activity model."""
    id: str
    activity_type: ActivityType
    student_id: str
    student_name: Optional[str] = None
    teacher_id: Optional[str] = None
    teacher_name: Optional[str] = None
    timestamp: datetime
    notes: Optional[str] = None
    room_id: Optional[str] = None
    
    
class DiaperActivity(BaseActivity):
    """Diaper change activity."""
    activity_type: ActivityType = ActivityType.DIAPER
    diaper_type: DiaperType
    has_cream: bool = False


class BottleActivity(BaseActivity):
    """Bottle feeding activity."""
    activity_type: ActivityType = ActivityType.BOTTLE
    amount_oz: float
    bottle_type: str = "milk"  # milk, formula, etc
    
    
class FoodActivity(BaseActivity):
    """Food/meal activity."""
    activity_type: ActivityType = ActivityType.FOOD
    meal_type: str  # breakfast, lunch, snack, dinner
    foods: List[str] = Field(default_factory=list)
    amount_eaten: Optional[str] = None  # all, most, some, none


class NapActivity(BaseActivity):
    """Nap/sleep activity."""
    activity_type: ActivityType = ActivityType.NAP
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None


class MoodActivity(BaseActivity):
    """Mood observation activity."""
    activity_type: ActivityType = ActivityType.MOOD
    mood: MoodType


class TemperatureActivity(BaseActivity):
    """Temperature check activity."""
    activity_type: ActivityType = ActivityType.TEMPERATURE
    temperature_f: float
    method: str = "forehead"  # forehead, ear, oral, etc


class PhotoActivity(BaseActivity):
    """Photo activity."""
    activity_type: ActivityType = ActivityType.PHOTO
    photo_urls: List[str] = Field(default_factory=list)
    caption: Optional[str] = None


class PottyActivity(BaseActivity):
    """Potty activity."""
    activity_type: ActivityType = ActivityType.POTTY
    success: bool
    potty_type: Optional[str] = None  # pee, poop, both


# Feed Models
class FeedItem(BaseModel):
    """Feed item containing an activity."""
    id: str
    created_at: datetime
    updated_at: datetime
    activity: Dict[str, Any]  # Can be any activity type
    likes_count: int = 0
    comments_count: int = 0
    is_liked: bool = False


class Feed(BaseModel):
    """Feed response."""
    items: List[FeedItem]
    has_more: bool
    next_cursor: Optional[str] = None


# Request/Response Models
class GetFeedRequest(BaseModel):
    """Request to get feed items."""
    student_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    activity_types: Optional[List[ActivityType]] = None
    limit: int = 50
    cursor: Optional[str] = None


class GetStudentsResponse(BaseModel):
    """Response for getting students."""
    students: List[Student]
    
    
class GetActivitiesResponse(BaseModel):
    """Response for getting activities."""
    activities: List[Dict[str, Any]]  # Various activity types
    has_more: bool
    next_cursor: Optional[str] = None