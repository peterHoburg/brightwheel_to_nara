"""Data transformation utilities between Brightwheel and Nara formats."""
from datetime import datetime
from typing import Dict, Any, Optional, List

from ..models.brightwheel import (
    ActivityType, DiaperActivity, BottleActivity, 
    FoodActivity, NapActivity, MoodActivity,
    TemperatureActivity, PhotoActivity, PottyActivity,
    DiaperType
)
from ..models.nara import (
    NaraActivityType, DiaperRecord, FeedingRecord,
    SleepRecord, HealthRecord, PhotoRecord,
    DiaperStatus, FeedingType, SleepType
)


def transform_diaper_activity(brightwheel_activity: Dict[str, Any]) -> DiaperRecord:
    """
    Transform Brightwheel diaper activity to Nara format.
    
    Args:
        brightwheel_activity: Brightwheel diaper activity data
        
    Returns:
        Nara DiaperRecord
    """
    # Map Brightwheel diaper types to Nara
    diaper_map = {
        DiaperType.WET: DiaperStatus.WET,
        DiaperType.BM: DiaperStatus.DIRTY,
        DiaperType.WET_BM: DiaperStatus.BOTH,
        DiaperType.DRY: DiaperStatus.DRY
    }
    
    diaper_type = brightwheel_activity.get('diaper_type', 'wet')
    nara_status = diaper_map.get(diaper_type, DiaperStatus.WET)
    
    return DiaperRecord(
        baby_id="",  # Will be set by caller
        timestamp=datetime.fromisoformat(brightwheel_activity['timestamp']),
        status=nara_status,
        cream_applied=brightwheel_activity.get('has_cream', False),
        notes=brightwheel_activity.get('notes')
    )


def transform_bottle_activity(brightwheel_activity: Dict[str, Any]) -> FeedingRecord:
    """
    Transform Brightwheel bottle activity to Nara feeding record.
    
    Args:
        brightwheel_activity: Brightwheel bottle activity data
        
    Returns:
        Nara FeedingRecord
    """
    bottle_type = brightwheel_activity.get('bottle_type', 'milk')
    
    # Map bottle types to Nara feeding types
    feeding_type = FeedingType.BOTTLE
    if bottle_type == 'formula':
        feeding_type = FeedingType.FORMULA
    elif bottle_type == 'pumped':
        feeding_type = FeedingType.PUMPED
        
    amount_oz = brightwheel_activity.get('amount_oz', 0)
    amount_ml = amount_oz * 29.5735  # Convert oz to ml
    
    return FeedingRecord(
        baby_id="",  # Will be set by caller
        timestamp=datetime.fromisoformat(brightwheel_activity['timestamp']),
        feeding_type=feeding_type,
        amount_ml=amount_ml,
        notes=brightwheel_activity.get('notes')
    )


def transform_food_activity(brightwheel_activity: Dict[str, Any]) -> FeedingRecord:
    """
    Transform Brightwheel food activity to Nara feeding record.
    
    Args:
        brightwheel_activity: Brightwheel food activity data
        
    Returns:
        Nara FeedingRecord
    """
    return FeedingRecord(
        baby_id="",  # Will be set by caller
        timestamp=datetime.fromisoformat(brightwheel_activity['timestamp']),
        feeding_type=FeedingType.SOLID,
        food_items=brightwheel_activity.get('foods', []),
        notes=f"{brightwheel_activity.get('meal_type', 'meal')}: "
               f"{brightwheel_activity.get('amount_eaten', 'some')} eaten. "
               f"{brightwheel_activity.get('notes', '')}"
    )


def transform_nap_activity(brightwheel_activity: Dict[str, Any]) -> SleepRecord:
    """
    Transform Brightwheel nap activity to Nara sleep record.
    
    Args:
        brightwheel_activity: Brightwheel nap activity data
        
    Returns:
        Nara SleepRecord
    """
    start_time = datetime.fromisoformat(brightwheel_activity['start_time'])
    end_time = None
    duration_minutes = None
    
    if brightwheel_activity.get('end_time'):
        end_time = datetime.fromisoformat(brightwheel_activity['end_time'])
        duration_minutes = int((end_time - start_time).total_seconds() / 60)
    elif brightwheel_activity.get('duration_minutes'):
        duration_minutes = brightwheel_activity['duration_minutes']
        
    return SleepRecord(
        baby_id="",  # Will be set by caller
        timestamp=start_time,
        sleep_type=SleepType.NAP,
        start_time=start_time,
        end_time=end_time,
        duration_minutes=duration_minutes,
        notes=brightwheel_activity.get('notes')
    )


def transform_temperature_activity(brightwheel_activity: Dict[str, Any]) -> HealthRecord:
    """
    Transform Brightwheel temperature activity to Nara health record.
    
    Args:
        brightwheel_activity: Brightwheel temperature activity data
        
    Returns:
        Nara HealthRecord
    """
    temp_f = brightwheel_activity.get('temperature_f', 98.6)
    temp_c = (temp_f - 32) * 5 / 9  # Convert F to C
    
    return HealthRecord(
        baby_id="",  # Will be set by caller
        timestamp=datetime.fromisoformat(brightwheel_activity['timestamp']),
        temperature_celsius=temp_c,
        notes=f"Temperature taken via {brightwheel_activity.get('method', 'forehead')}. "
               f"{brightwheel_activity.get('notes', '')}"
    )


def transform_photo_activity(brightwheel_activity: Dict[str, Any]) -> PhotoRecord:
    """
    Transform Brightwheel photo activity to Nara photo record.
    
    Args:
        brightwheel_activity: Brightwheel photo activity data
        
    Returns:
        Nara PhotoRecord
    """
    photo_urls = brightwheel_activity.get('photo_urls', [])
    photo_url = photo_urls[0] if photo_urls else ""
    
    return PhotoRecord(
        baby_id="",  # Will be set by caller
        timestamp=datetime.fromisoformat(brightwheel_activity['timestamp']),
        photo_url=photo_url,
        caption=brightwheel_activity.get('caption') or brightwheel_activity.get('notes')
    )


def transform_activity(brightwheel_activity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Transform a Brightwheel activity to Nara format.
    
    Args:
        brightwheel_activity: Brightwheel activity data
        
    Returns:
        Nara activity record or None if not supported
    """
    activity_type = brightwheel_activity.get('activity_type')
    
    transformers = {
        ActivityType.DIAPER: transform_diaper_activity,
        ActivityType.BOTTLE: transform_bottle_activity,
        ActivityType.FOOD: transform_food_activity,
        ActivityType.NAP: transform_nap_activity,
        ActivityType.TEMPERATURE: transform_temperature_activity,
        ActivityType.PHOTO: transform_photo_activity
    }
    
    transformer = transformers.get(activity_type)
    if transformer:
        nara_activity = transformer(brightwheel_activity)
        return nara_activity.model_dump()
    
    return None


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return celsius * 9 / 5 + 32


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convert Fahrenheit to Celsius."""
    return (fahrenheit - 32) * 5 / 9


def oz_to_ml(oz: float) -> float:
    """Convert ounces to milliliters."""
    return oz * 29.5735


def ml_to_oz(ml: float) -> float:
    """Convert milliliters to ounces."""
    return ml / 29.5735