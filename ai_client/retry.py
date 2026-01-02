"""
Retry logic for AI client operations
"""

import asyncio
import time
import random
from typing import Callable, TypeVar, Any, Optional
from functools import wraps

from .exceptions import AIRateLimitError, AIProviderError

T = TypeVar('T')


def exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
):
    """Decorator for exponential backoff retry logic
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
        max_delay: Maximum delay in seconds
        jitter: Add random jitter to delay
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (AIRateLimitError, ConnectionError, TimeoutError) as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    
                    # Add jitter to prevent thundering herd
                    if jitter:
                        delay += random.uniform(0, delay * 0.1)
                    
                    time.sleep(delay)
                except Exception as e:
                    # Don't retry on non-recoverable errors
                    raise
            
            # This shouldn't be reached, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


def async_exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
):
    """Async version of exponential backoff decorator"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except (AIRateLimitError, ConnectionError, TimeoutError) as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    
                    # Add jitter to prevent thundering herd
                    if jitter:
                        delay += random.uniform(0, delay * 0.1)
                    
                    await asyncio.sleep(delay)
                except Exception as e:
                    # Don't retry on non-recoverable errors
                    raise
            
            # This shouldn't be reached, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator