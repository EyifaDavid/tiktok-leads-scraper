"""Retry logic with exponential backoff and jitter."""

import asyncio
import random
import logging
from typing import Callable, Any, Optional, Type

logger = logging.getLogger(__name__)


def backoff_seconds(attempt: int, base: float = 0.8, cap: float = 30.0) -> float:
    """Calculate exponential backoff with jitter.
    
    Args:
        attempt: Current attempt number (1-indexed)
        base: Base delay in seconds
        cap: Maximum delay in seconds
    
    Returns:
        Delay in seconds with jitter
    """
    exp = min(cap, base * (2 ** (attempt - 1)))
    jitter = random.uniform(0, exp * 0.2)
    return exp + jitter


def is_transient_error(exception: Exception) -> bool:
    """Check if error is transient and should be retried.
    
    Args:
        exception: The exception to check
    
    Returns:
        True if the error is transient and should be retried
    """
    from tiktok_leads.exceptions import RateLimitError, SoftBlockError
    
    transient_exceptions = (
        ConnectionError,
        TimeoutError,
        OSError,
        RateLimitError,
        SoftBlockError,
    )
    
    if isinstance(exception, transient_exceptions):
        return True
    
    if hasattr(exception, 'status'):
        status = getattr(exception, 'status', 0)
        if status in (429, 408, 500, 502, 503, 504):
            return True
    
    return False


def is_deterministic_error(exception: Exception) -> bool:
    """Check if error is deterministic and should NOT be retried.
    
    Args:
        exception: The exception to check
    
    Returns:
        True if the error is deterministic and should not be retried
    """
    from tiktok_leads.exceptions import ConfigurationError
    
    deterministic_exceptions = (
        ValueError,
        KeyError,
        ConfigurationError,
    )
    
    if isinstance(exception, deterministic_exceptions):
        return True
    
    if hasattr(exception, 'status'):
        status = getattr(exception, 'status', 0)
        if status in (401, 403, 404):
            return True
    
    return False


async def retry_async(
    func: Callable,
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retryable_exceptions: Optional[tuple] = None,
    **kwargs
) -> Any:
    """Execute async function with retry logic.
    
    Args:
        func: Async function to execute
        *args: Positional arguments for the function
        max_retries: Maximum number of retries
        base_delay: Base delay for exponential backoff
        max_delay: Maximum delay between retries
        retryable_exceptions: Tuple of exceptions to retry on (None = use default)
        **kwargs: Keyword arguments for the function
    
    Returns:
        Result of the function
    
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(1, max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            if is_deterministic_error(e):
                logger.error(f"Deterministic error on attempt {attempt}: {e}")
                raise
            
            if attempt == max_retries:
                logger.error(f"All {max_retries} attempts failed. Last error: {e}")
                raise
            
            if is_transient_error(e):
                delay = backoff_seconds(attempt, base_delay, max_delay)
                logger.warning(
                    f"Transient error on attempt {attempt}/{max_retries}: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)
            else:
                logger.warning(
                    f"Non-transient error on attempt {attempt}/{max_retries}: {e}. "
                    f"Retrying anyway..."
                )
                delay = backoff_seconds(attempt, base_delay, max_delay)
                await asyncio.sleep(delay)
    
    raise last_exception
