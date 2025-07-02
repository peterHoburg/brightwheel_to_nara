"""Error handling and retry utilities."""
import asyncio
import functools
from typing import Type, Tuple, Optional, Callable, Any
import httpx


class BrightwheelError(Exception):
    """Base exception for Brightwheel API errors."""
    pass


class AuthenticationError(BrightwheelError):
    """Authentication related errors."""
    pass


class RateLimitError(BrightwheelError):
    """Rate limit exceeded error."""
    pass


class NaraError(Exception):
    """Base exception for Nara API errors."""
    pass


class TransferError(Exception):
    """Error during data transfer between platforms."""
    pass


def handle_http_errors(func: Callable) -> Callable:
    """
    Decorator to handle HTTP errors from API calls.
    
    Args:
        func: Async function to wrap
        
    Returns:
        Wrapped function with error handling
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Authentication failed. Please login again.")
            elif e.response.status_code == 429:
                raise RateLimitError("Rate limit exceeded. Please try again later.")
            elif e.response.status_code >= 500:
                raise BrightwheelError(f"Server error: {e.response.status_code}")
            else:
                raise BrightwheelError(f"HTTP error: {e.response.status_code} - {e.response.text}")
        except httpx.TimeoutException:
            raise BrightwheelError("Request timed out. Please try again.")
        except httpx.NetworkError:
            raise BrightwheelError("Network error. Please check your connection.")
    
    return wrapper


async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Any:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retries
        initial_delay: Initial delay in seconds
        backoff_factor: Factor to multiply delay by for each retry
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Result of the function
        
    Raises:
        Last exception if all retries fail
    """
    delay = initial_delay
    last_exception: Optional[Exception] = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            if attempt < max_retries:
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
                delay *= backoff_factor
            else:
                print(f"All {max_retries + 1} attempts failed.")
    
    if last_exception:
        raise last_exception


class ErrorLogger:
    """Log errors during transfer process."""
    
    def __init__(self):
        """Initialize error logger."""
        self.errors: list[dict] = []
        
    def log_error(
        self, 
        activity_id: str,
        activity_type: str,
        error: Exception,
        context: Optional[dict] = None
    ):
        """
        Log an error.
        
        Args:
            activity_id: ID of the activity that failed
            activity_type: Type of activity
            error: The exception that occurred
            context: Additional context information
        """
        self.errors.append({
            'activity_id': activity_id,
            'activity_type': activity_type,
            'error': str(error),
            'error_type': type(error).__name__,
            'context': context or {}
        })
        
    def get_errors(self) -> list[dict]:
        """Get all logged errors."""
        return self.errors
    
    def clear_errors(self):
        """Clear all logged errors."""
        self.errors.clear()
        
    def has_errors(self) -> bool:
        """Check if any errors have been logged."""
        return len(self.errors) > 0
    
    def get_error_summary(self) -> dict:
        """Get a summary of errors by type."""
        summary = {}
        for error in self.errors:
            error_type = error['error_type']
            if error_type not in summary:
                summary[error_type] = 0
            summary[error_type] += 1
        return summary