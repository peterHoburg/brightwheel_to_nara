"""Brightwheel API client implementation."""
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import httpx
from playwright.async_api import async_playwright, Page
import json

from ..models.brightwheel import (
    LoginRequest, LoginResponse, Session,
    Student, GetStudentsResponse, 
    Feed, GetFeedRequest,
    ActivityType
)


class BrightwheelClient:
    """Client for interacting with Brightwheel API."""
    
    BASE_URL = "https://schools.mybrightwheel.com"
    API_BASE = f"{BASE_URL}/api/v1"
    
    def __init__(self):
        """Initialize the Brightwheel client."""
        self.session: Optional[Session] = None
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
            
    async def login_with_cookie(self, session_cookie: str) -> Session:
        """
        Login to Brightwheel using a session cookie.
        
        Args:
            session_cookie: The _brightwheel_v2 cookie value
            
        Returns:
            Session object with auth tokens
        """
        # Set the cookie in the HTTP client
        self.http_client.cookies.set('_brightwheel_v2', session_cookie, domain='.mybrightwheel.com')
        
        # Verify the session is valid by making a test request
        try:
            response = await self.http_client.get(f"{self.API_BASE}/me")
            response.raise_for_status()
            
            user_data = response.json()
            user_id = user_data.get('id', '')
            
            # Create session object
            self.session = Session(
                token=session_cookie,
                cookies={'_brightwheel_v2': session_cookie},
                expires_at=datetime.utcnow() + timedelta(hours=24),
                user_id=user_id
            )
            
            return self.session
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError("Invalid session cookie. Please login again.")
            raise
    
    async def login(self, username: str, password: str) -> Session:
        """
        Login to Brightwheel using Playwright to handle captcha.
        
        Args:
            username: Email or phone number
            password: User password
            
        Returns:
            Session object with auth tokens
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Show browser for captcha
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Navigate to login page
                await page.goto(f"{self.BASE_URL}/sign-in")
                
                # Fill in credentials
                await page.fill('input[data-testid="username-input"]', username)
                await page.fill('input[data-testid="password-input"]', password)
                
                # Click sign in
                await page.click('button[data-testid="sign-in-button"]')
                
                # Wait for either successful login or captcha
                # Give user time to solve captcha if needed
                print("Please solve the captcha if prompted...")
                
                # Wait for navigation after login
                try:
                    await page.wait_for_url("**/feed", timeout=60000)  # 60 second timeout
                except:
                    # May redirect to different page based on user type
                    await page.wait_for_function(
                        "window.location.pathname !== '/sign-in'",
                        timeout=60000
                    )
                
                # Extract cookies and session info
                cookies = await context.cookies()
                cookie_dict = {c['name']: c['value'] for c in cookies}
                
                # Get auth token from localStorage or cookies
                session_token = None
                try:
                    # Try to get from localStorage
                    session_token = await page.evaluate(
                        "() => localStorage.getItem('authToken') || localStorage.getItem('sessionToken')"
                    )
                except:
                    pass
                    
                if not session_token:
                    # Look for session cookie
                    session_token = cookie_dict.get('_brightwheel_v2', '')
                
                # Create session object
                self.session = Session(
                    token=session_token,
                    cookies=cookie_dict,
                    expires_at=datetime.utcnow() + timedelta(hours=24),
                    user_id=""  # Will be populated from API call
                )
                
                # Update HTTP client with cookies
                if self.http_client:
                    self.http_client.cookies.update(cookie_dict)
                    if session_token:
                        self.http_client.headers['Authorization'] = f"Bearer {session_token}"
                
                return self.session
                
            finally:
                await browser.close()
    
    def _check_session(self):
        """Check if session is valid."""
        if not self.session:
            raise ValueError("Not authenticated. Please login first.")
        if self.session.expires_at < datetime.utcnow():
            raise ValueError("Session expired. Please login again.")
    
    async def get_students(self) -> List[Student]:
        """
        Get list of students/children.
        
        Returns:
            List of Student objects
        """
        self._check_session()
        
        response = await self.http_client.get(
            f"{self.API_BASE}/students",
            params={"include": "guardians,room"}
        )
        response.raise_for_status()
        
        data = response.json()
        students = []
        
        for student_data in data.get('students', []):
            student = Student(
                id=student_data['id'],
                first_name=student_data['first_name'],
                last_name=student_data['last_name'],
                birthdate=datetime.fromisoformat(student_data['birthdate']),
                room_id=student_data.get('room_id'),
                room_name=student_data.get('room', {}).get('name'),
                guardian_ids=[g['id'] for g in student_data.get('guardians', [])],
                profile_photo_url=student_data.get('profile_photo_url'),
                allergies=student_data.get('allergies', []),
                medical_notes=student_data.get('medical_notes'),
                enrollment_status=student_data.get('enrollment_status', 'active')
            )
            students.append(student)
            
        return students
    
    async def get_student_feed(
        self, 
        student_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        activity_types: Optional[List[ActivityType]] = None,
        limit: int = 50
    ) -> Feed:
        """
        Get activity feed for a student.
        
        Args:
            student_id: ID of the student
            start_date: Start date for activities
            end_date: End date for activities
            activity_types: Filter by activity types
            limit: Number of items to fetch
            
        Returns:
            Feed object with activities
        """
        self._check_session()
        
        params = {
            "student_id": student_id,
            "limit": limit
        }
        
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        if activity_types:
            params["activity_types"] = ",".join(activity_types)
            
        response = await self.http_client.get(
            f"{self.API_BASE}/feed",
            params=params
        )
        response.raise_for_status()
        
        data = response.json()
        
        return Feed(
            items=[],  # Would parse individual items here
            has_more=data.get('has_more', False),
            next_cursor=data.get('next_cursor')
        )
    
    async def get_activities(
        self,
        student_id: str,
        start_date: datetime,
        end_date: datetime,
        activity_type: Optional[ActivityType] = None
    ) -> List[Dict[str, Any]]:
        """
        Get activities for a student within a date range.
        
        Args:
            student_id: ID of the student
            start_date: Start date
            end_date: End date  
            activity_type: Optional filter by type
            
        Returns:
            List of activity dictionaries
        """
        self._check_session()
        
        params = {
            "student_id": student_id,
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat()
        }
        
        if activity_type:
            params["activity_type"] = activity_type
            
        response = await self.http_client.get(
            f"{self.API_BASE}/activities",
            params=params
        )
        response.raise_for_status()
        
        return response.json().get('activities', [])