"""Nara Baby Tracker API client implementation."""
from datetime import datetime
from typing import Optional, List, Dict, Any
import httpx

from ..models.nara import (
    NaraLoginRequest, NaraLoginResponse,
    Baby, NaraActivityType,
    CreateActivityRequest, CreateActivityResponse,
    GetActivitiesRequest, GetActivitiesResponse,
    DiaperRecord, FeedingRecord, SleepRecord,
    HealthRecord, MeasurementRecord, PhotoRecord,
    MilestoneRecord, PumpingRecord, TummyTimeRecord,
    PlayRecord
)


class NaraClient:
    """Client for interacting with Nara Baby Tracker API."""
    
    BASE_URL = "https://api.nara.com"  # This would be the actual API URL
    
    def __init__(self):
        """Initialize the Nara client."""
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.http_client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=30.0,
            follow_redirects=True
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.http_client:
            await self.http_client.aclose()
            
    async def login(self, email: str, password: str) -> NaraLoginResponse:
        """
        Login to Nara.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Login response with tokens
        """
        request = NaraLoginRequest(email=email, password=password)
        
        response = await self.http_client.post(
            "/auth/login",
            json=request.model_dump()
        )
        response.raise_for_status()
        
        login_response = NaraLoginResponse(**response.json())
        
        # Store tokens
        self.access_token = login_response.access_token
        self.refresh_token = login_response.refresh_token
        
        # Update headers
        self.http_client.headers['Authorization'] = f"Bearer {self.access_token}"
        
        return login_response
    
    def _check_auth(self):
        """Check if authenticated."""
        if not self.access_token:
            raise ValueError("Not authenticated. Please login first.")
    
    async def get_babies(self) -> List[Baby]:
        """
        Get list of babies/children.
        
        Returns:
            List of Baby objects
        """
        self._check_auth()
        
        response = await self.http_client.get("/babies")
        response.raise_for_status()
        
        data = response.json()
        return [Baby(**baby_data) for baby_data in data.get('babies', [])]
    
    async def create_diaper_activity(
        self,
        baby_id: str,
        diaper_record: DiaperRecord
    ) -> CreateActivityResponse:
        """
        Create a diaper change record.
        
        Args:
            baby_id: ID of the baby
            diaper_record: Diaper record data
            
        Returns:
            Response with created activity
        """
        self._check_auth()
        
        diaper_record.baby_id = baby_id
        
        response = await self.http_client.post(
            f"/babies/{baby_id}/activities/diaper",
            json=diaper_record.model_dump()
        )
        response.raise_for_status()
        
        return CreateActivityResponse(**response.json())
    
    async def create_feeding_activity(
        self,
        baby_id: str,
        feeding_record: FeedingRecord
    ) -> CreateActivityResponse:
        """
        Create a feeding record.
        
        Args:
            baby_id: ID of the baby
            feeding_record: Feeding record data
            
        Returns:
            Response with created activity
        """
        self._check_auth()
        
        feeding_record.baby_id = baby_id
        
        response = await self.http_client.post(
            f"/babies/{baby_id}/activities/feeding",
            json=feeding_record.model_dump()
        )
        response.raise_for_status()
        
        return CreateActivityResponse(**response.json())
    
    async def create_sleep_activity(
        self,
        baby_id: str,
        sleep_record: SleepRecord
    ) -> CreateActivityResponse:
        """
        Create a sleep record.
        
        Args:
            baby_id: ID of the baby
            sleep_record: Sleep record data
            
        Returns:
            Response with created activity
        """
        self._check_auth()
        
        sleep_record.baby_id = baby_id
        
        response = await self.http_client.post(
            f"/babies/{baby_id}/activities/sleep",
            json=sleep_record.model_dump()
        )
        response.raise_for_status()
        
        return CreateActivityResponse(**response.json())
    
    async def create_generic_activity(
        self,
        baby_id: str,
        activity: Dict[str, Any]
    ) -> CreateActivityResponse:
        """
        Create a generic activity record.
        
        Args:
            baby_id: ID of the baby
            activity: Activity data as dictionary
            
        Returns:
            Response with created activity
        """
        self._check_auth()
        
        activity['baby_id'] = baby_id
        
        response = await self.http_client.post(
            f"/babies/{baby_id}/activities",
            json=activity
        )
        response.raise_for_status()
        
        return CreateActivityResponse(**response.json())
    
    async def get_activities(
        self,
        baby_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        activity_types: Optional[List[NaraActivityType]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> GetActivitiesResponse:
        """
        Get activities for a baby.
        
        Args:
            baby_id: ID of the baby
            start_date: Start date filter
            end_date: End date filter
            activity_types: Filter by activity types
            limit: Number of records to return
            offset: Pagination offset
            
        Returns:
            Activities response
        """
        self._check_auth()
        
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        if activity_types:
            params["activity_types"] = ",".join(activity_types)
            
        response = await self.http_client.get(
            f"/babies/{baby_id}/activities",
            params=params
        )
        response.raise_for_status()
        
        data = response.json()
        
        return GetActivitiesResponse(
            activities=data.get('activities', []),
            total_count=data.get('total_count', 0),
            has_more=data.get('has_more', False)
        )
    
    async def upload_photo(
        self,
        baby_id: str,
        photo_path: str,
        caption: Optional[str] = None
    ) -> str:
        """
        Upload a photo for a baby.
        
        Args:
            baby_id: ID of the baby
            photo_path: Path to the photo file
            caption: Optional photo caption
            
        Returns:
            URL of the uploaded photo
        """
        self._check_auth()
        
        with open(photo_path, 'rb') as f:
            files = {'photo': f}
            data = {}
            if caption:
                data['caption'] = caption
                
            response = await self.http_client.post(
                f"/babies/{baby_id}/photos",
                files=files,
                data=data
            )
            response.raise_for_status()
            
        return response.json().get('photo_url', '')