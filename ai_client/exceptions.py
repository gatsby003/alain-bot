"""
Custom exceptions for AI client
"""

from typing import Optional, Any


class AIClientError(Exception):
    """Base exception for AI client errors"""
    pass


class AIProviderError(AIClientError):
    """Error from an AI provider"""
    
    def __init__(
        self, 
        message: str, 
        provider: str,
        original_error: Optional[Exception] = None,
        status_code: Optional[int] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.original_error = original_error
        self.status_code = status_code


class AIRateLimitError(AIProviderError):
    """Rate limit exceeded error"""
    pass


class AIAuthenticationError(AIProviderError):
    """Authentication error"""
    pass


class AIModelNotFoundError(AIProviderError):
    """Model not found error"""
    pass


class AIQuotaExceededError(AIProviderError):
    """Quota exceeded error"""
    pass


class AIConfigurationError(AIClientError):
    """Configuration error"""
    pass