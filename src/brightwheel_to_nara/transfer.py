"""Main transfer logic for syncing data from Brightwheel to Nara."""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

from .api import BrightwheelClient, NaraClient
from .config import get_settings, ACTIVITY_TYPE_MAPPING
from .utils import (
    transform_activity,
    ErrorLogger,
    retry_with_backoff,
    TransferError
)
from .models.brightwheel import Student, ActivityType
from .models.nara import Baby, NaraActivityType


logger = logging.getLogger(__name__)


class DataTransfer:
    """Orchestrates data transfer from Brightwheel to Nara."""
    
    def __init__(self):
        """Initialize the data transfer."""
        self.settings = get_settings()
        self.brightwheel_client = BrightwheelClient()
        self.nara_client = NaraClient()
        self.error_logger = ErrorLogger()
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.brightwheel_client.__aenter__()
        await self.nara_client.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.brightwheel_client.__aexit__(exc_type, exc_val, exc_tb)
        await self.nara_client.__aexit__(exc_type, exc_val, exc_tb)
        
    async def authenticate(self):
        """Authenticate with both platforms."""
        logger.info("Authenticating with Brightwheel...")
        
        # Try cookie-based auth first if available
        if self.settings.brightwheel_session_cookie:
            try:
                logger.info("Attempting authentication with session cookie...")
                await self.brightwheel_client.login_with_cookie(
                    self.settings.brightwheel_session_cookie
                )
                logger.info("Successfully authenticated with Brightwheel using session cookie")
            except ValueError as e:
                logger.warning(f"Cookie authentication failed: {e}")
                logger.info("Falling back to interactive login...")
                await self.brightwheel_client.login(
                    self.settings.brightwheel_username,
                    self.settings.brightwheel_password
                )
                logger.info("Successfully authenticated with Brightwheel using interactive login")
        else:
            # Use interactive login
            await self.brightwheel_client.login(
                self.settings.brightwheel_username,
                self.settings.brightwheel_password
            )
            logger.info("Successfully authenticated with Brightwheel using interactive login")
        
        if self.settings.nara_email and self.settings.nara_password:
            logger.info("Authenticating with Nara...")
            await self.nara_client.login(
                self.settings.nara_email,
                self.settings.nara_password
            )
            logger.info("Successfully authenticated with Nara")
        else:
            logger.warning("Nara credentials not provided. Running in read-only mode.")
            
    async def map_students_to_babies(
        self,
        students: List[Student],
        babies: List[Baby]
    ) -> Dict[str, str]:
        """
        Map Brightwheel students to Nara babies.
        
        Args:
            students: List of Brightwheel students
            babies: List of Nara babies
            
        Returns:
            Mapping of student_id to baby_id
        """
        mapping = {}
        
        for student in students:
            # Try to match by name and birthdate
            for baby in babies:
                if (student.first_name.lower() == baby.name.split()[0].lower() and
                    student.birthdate.date() == baby.birth_date.date()):
                    mapping[student.id] = baby.id
                    logger.info(f"Mapped {student.first_name} {student.last_name} to {baby.name}")
                    break
            else:
                logger.warning(f"Could not find matching baby for {student.first_name} {student.last_name}")
                
        return mapping
    
    async def transfer_activity(
        self,
        activity: Dict[str, Any],
        baby_id: str
    ) -> bool:
        """
        Transfer a single activity to Nara.
        
        Args:
            activity: Brightwheel activity data
            baby_id: Nara baby ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Transform the activity
            nara_activity = transform_activity(activity)
            if not nara_activity:
                logger.debug(f"Skipping unsupported activity type: {activity.get('activity_type')}")
                return False
                
            # Set the baby ID
            nara_activity['baby_id'] = baby_id
            
            # Skip if dry run
            if self.settings.dry_run:
                logger.info(f"[DRY RUN] Would create {nara_activity['activity_type']} activity")
                return True
                
            # Create the activity in Nara
            await retry_with_backoff(
                lambda: self.nara_client.create_generic_activity(baby_id, nara_activity),
                max_retries=self.settings.retry_max_attempts,
                initial_delay=self.settings.retry_delay_seconds
            )
            
            logger.debug(f"Successfully transferred {activity.get('activity_type')} activity")
            return True
            
        except Exception as e:
            self.error_logger.log_error(
                activity_id=activity.get('id', 'unknown'),
                activity_type=activity.get('activity_type', 'unknown'),
                error=e,
                context={'baby_id': baby_id}
            )
            logger.error(f"Failed to transfer activity: {e}")
            return False
    
    async def sync_student_activities(
        self,
        student: Student,
        baby_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, int]:
        """
        Sync activities for a single student.
        
        Args:
            student: Brightwheel student
            baby_id: Corresponding Nara baby ID
            start_date: Start date for sync
            end_date: End date for sync
            
        Returns:
            Statistics about the sync
        """
        stats = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0
        }
        
        logger.info(f"Syncing activities for {student.first_name} {student.last_name}")
        
        # Get activities from Brightwheel
        activities = await self.brightwheel_client.get_activities(
            student_id=student.id,
            start_date=start_date,
            end_date=end_date
        )
        
        stats['total'] = len(activities)
        logger.info(f"Found {len(activities)} activities to sync")
        
        # Process in batches
        batch_size = self.settings.batch_size
        for i in range(0, len(activities), batch_size):
            batch = activities[i:i + batch_size]
            
            # Process batch concurrently
            tasks = [
                self.transfer_activity(activity, baby_id)
                for activity in batch
            ]
            results = await asyncio.gather(*tasks)
            
            # Update statistics
            for success in results:
                if success is True:
                    stats['successful'] += 1
                elif success is False:
                    stats['failed'] += 1
                else:
                    stats['skipped'] += 1
                    
        return stats
    
    async def run(self):
        """Run the full transfer process."""
        try:
            # Authenticate
            await self.authenticate()
            
            # Get students from Brightwheel
            logger.info("Fetching students from Brightwheel...")
            students = await self.brightwheel_client.get_students()
            logger.info(f"Found {len(students)} students")
            
            if not students:
                logger.warning("No students found. Nothing to sync.")
                return
                
            # Get babies from Nara (if authenticated)
            babies = []
            student_baby_mapping = {}
            
            if self.nara_client.access_token:
                logger.info("Fetching babies from Nara...")
                babies = await self.nara_client.get_babies()
                logger.info(f"Found {len(babies)} babies")
                
                # Map students to babies
                student_baby_mapping = await self.map_students_to_babies(students, babies)
                
                if not student_baby_mapping:
                    logger.error("Could not map any students to babies. Aborting.")
                    return
            else:
                logger.info("Running in read-only mode. Skipping Nara operations.")
                
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=self.settings.sync_days_back)
            
            logger.info(f"Syncing activities from {start_date.date()} to {end_date.date()}")
            
            # Sync each student
            total_stats = {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0
            }
            
            for student in students:
                baby_id = student_baby_mapping.get(student.id)
                if not baby_id:
                    logger.warning(f"Skipping {student.first_name} {student.last_name} - no matching baby")
                    continue
                    
                stats = await self.sync_student_activities(
                    student=student,
                    baby_id=baby_id,
                    start_date=start_date,
                    end_date=end_date
                )
                
                # Update total statistics
                for key in total_stats:
                    total_stats[key] += stats[key]
                    
            # Log summary
            logger.info("=" * 50)
            logger.info("TRANSFER COMPLETE")
            logger.info(f"Total activities: {total_stats['total']}")
            logger.info(f"Successful: {total_stats['successful']}")
            logger.info(f"Failed: {total_stats['failed']}")
            logger.info(f"Skipped: {total_stats['skipped']}")
            
            if self.error_logger.has_errors():
                logger.warning(f"Errors occurred during transfer: {self.error_logger.get_error_summary()}")
                
        except Exception as e:
            logger.error(f"Transfer failed: {e}")
            raise TransferError(f"Transfer failed: {e}") from e


async def main():
    """Main entry point for the transfer process."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async with DataTransfer() as transfer:
        await transfer.run()