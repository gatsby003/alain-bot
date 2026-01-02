"""
Base interfaces and types for AI client abstraction
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Protocol, runtime_checkable


@dataclass
class AIMessage:
    """Represents a message in a conversation"""
    role: str  # "user", "assistant", "system"
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class AIResponse:
    """Standardized response from any AI provider"""
    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    raw_response: Optional[Any] = None
    
    @property
    def text(self) -> str:
        """Alias for content for easier access"""
        return self.content


@runtime_checkable
class AIProvider(Protocol):
    """Protocol defining the interface all AI providers must implement"""
    
    @abstractmethod
    async def generate(
        self,
        messages: List[AIMessage],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> AIResponse:
        """Generate a response from the AI provider"""
        ...
    
    @abstractmethod
    def generate_sync(
        self,
        messages: List[AIMessage],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> AIResponse:
        """Synchronous version of generate"""
        ...
    
    @property
    @abstractmethod
    def default_model(self) -> str:
        """Return the default model for this provider"""
        ...
    
    @property
    @abstractmethod
    def available_models(self) -> List[str]:
        """Return list of available models for this provider"""
        ...


class BaseAIProvider(ABC):
    """Abstract base class providing common functionality for AI providers"""
    
    def __init__(self, api_key: Optional[str] = None, **config):
        self.api_key = api_key
        self.config = config
    
    def _validate_messages(self, messages: List[AIMessage]) -> None:
        """Validate message format"""
        if not messages:
            raise ValueError("Messages list cannot be empty")
        
        valid_roles = {"user", "assistant", "system"}
        for msg in messages:
            if msg.role not in valid_roles:
                raise ValueError(f"Invalid role: {msg.role}. Must be one of {valid_roles}")
            if not msg.content.strip():
                raise ValueError("Message content cannot be empty")
    
    def _prepare_messages(self, messages: List[AIMessage]) -> List[Dict[str, str]]:
        """Convert AIMessage objects to dict format"""
        self._validate_messages(messages)
        return [msg.to_dict() for msg in messages]
    
    @abstractmethod
    async def generate(self, messages: List[AIMessage], **kwargs) -> AIResponse:
        """Generate a response from the AI provider"""
        pass
    
    @abstractmethod
    def generate_sync(self, messages: List[AIMessage], **kwargs) -> AIResponse:
        """Synchronous version of generate"""
        pass