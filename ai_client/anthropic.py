"""
Anthropic Claude provider implementation using the official SDK.
"""

import os
from typing import List, Optional, Dict, Any
import anthropic

from .base import BaseAIProvider, AIMessage, AIResponse
from .exceptions import (
    AIProviderError, AIRateLimitError, AIAuthenticationError, 
    AIModelNotFoundError, AIQuotaExceededError
)


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude provider implementation using async client."""
    
    def __init__(self, api_key: Optional[str] = None, **config):
        super().__init__(api_key, **config)
        
        # Use provided API key or fall back to environment variable
        key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY or pass api_key parameter.")
        
        # Use async client for async operations
        self.async_client = anthropic.AsyncAnthropic(api_key=key)
        # Keep sync client for sync operations
        self.sync_client = anthropic.Anthropic(api_key=key)
        self._default_model = config.get("default_model", "claude-3-5-haiku-20241022")
    
    @property
    def default_model(self) -> str:
        return self._default_model
    
    @property
    def available_models(self) -> List[str]:
        return [
            "claude-sonnet-4-20250514",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022", 
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]
    
    async def generate(
        self,
        messages: List[AIMessage],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> AIResponse:
        """Generate response asynchronously using Anthropic's async client."""
        # Separate system message from conversation messages
        system_prompt, conversation_messages = self._separate_system_message(messages)
        
        # Set defaults
        model = model or self.default_model
        max_tokens = max_tokens or 1024
        
        # Build request parameters
        params: Dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": conversation_messages,
        }
        
        # Add system prompt if present
        if system_prompt:
            params["system"] = system_prompt
        
        # Add optional parameters if provided
        if temperature is not None:
            params["temperature"] = temperature
        
        # Add any additional kwargs passed through
        params.update(kwargs)
        
        try:
            # Call Anthropic API using async client
            response = await self.async_client.messages.create(**params)
            
            # Extract content from response
            content = ""
            if response.content:
                # Anthropic returns content as a list of content blocks
                content = "".join(
                    block.text if hasattr(block, 'text') else str(block) 
                    for block in response.content
                )
            
            # Extract usage information
            usage_info = self._extract_usage_info(response)
            
            return AIResponse(
                content=content,
                model=response.model,
                usage=usage_info,
                raw_response=response
            )
            
        except anthropic.RateLimitError as e:
            raise AIRateLimitError(
                f"Anthropic rate limit exceeded: {str(e)}", 
                provider="anthropic",
                original_error=e,
                status_code=getattr(e, 'status_code', None)
            ) from e
        except anthropic.AuthenticationError as e:
            raise AIAuthenticationError(
                f"Anthropic authentication failed: {str(e)}", 
                provider="anthropic",
                original_error=e,
                status_code=getattr(e, 'status_code', None)
            ) from e
        except anthropic.NotFoundError as e:
            if "model" in str(e).lower():
                raise AIModelNotFoundError(
                    f"Model not found: {model}. Available models: {', '.join(self.available_models)}", 
                    provider="anthropic",
                    original_error=e,
                    status_code=getattr(e, 'status_code', None)
                ) from e
            else:
                raise AIProviderError(
                    f"Anthropic API error: {str(e)}", 
                    provider="anthropic",
                    original_error=e,
                    status_code=getattr(e, 'status_code', None)
                ) from e
        except anthropic.BadRequestError as e:
            if "quota" in str(e).lower() or "limit" in str(e).lower():
                raise AIQuotaExceededError(
                    f"Anthropic quota exceeded: {str(e)}", 
                    provider="anthropic",
                    original_error=e,
                    status_code=getattr(e, 'status_code', None)
                ) from e
            else:
                raise AIProviderError(
                    f"Anthropic bad request: {str(e)}", 
                    provider="anthropic",
                    original_error=e,
                    status_code=getattr(e, 'status_code', None)
                ) from e
        except anthropic.APIError as e:
            raise AIProviderError(
                f"Anthropic API error: {str(e)}", 
                provider="anthropic",
                original_error=e,
                status_code=getattr(e, 'status_code', None)
            ) from e
        except Exception as e:
            raise AIProviderError(
                f"Unexpected error from Anthropic: {str(e)}", 
                provider="anthropic",
                original_error=e
            ) from e
    
    def generate_sync(
        self,
        messages: List[AIMessage],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> AIResponse:
        """Generate response synchronously."""
        # Separate system message from conversation messages
        system_prompt, conversation_messages = self._separate_system_message(messages)
        
        # Set defaults
        model = model or self.default_model
        max_tokens = max_tokens or 1024
        
        # Build request parameters
        params: Dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": conversation_messages,
        }
        
        # Add system prompt if present
        if system_prompt:
            params["system"] = system_prompt
        
        # Add optional parameters if provided
        if temperature is not None:
            params["temperature"] = temperature
        
        # Add any additional kwargs passed through
        params.update(kwargs)
        
        try:
            # Call Anthropic API
            response = self.sync_client.messages.create(**params)
            
            # Extract content from response
            content = ""
            if response.content:
                content = "".join(
                    block.text if hasattr(block, 'text') else str(block) 
                    for block in response.content
                )
            
            # Extract usage information
            usage_info = self._extract_usage_info(response)
            
            return AIResponse(
                content=content,
                model=response.model,
                usage=usage_info,
                raw_response=response
            )
            
        except anthropic.RateLimitError as e:
            raise AIRateLimitError(
                f"Anthropic rate limit exceeded: {str(e)}", 
                provider="anthropic",
                original_error=e,
                status_code=getattr(e, 'status_code', None)
            ) from e
        except anthropic.AuthenticationError as e:
            raise AIAuthenticationError(
                f"Anthropic authentication failed: {str(e)}", 
                provider="anthropic",
                original_error=e,
                status_code=getattr(e, 'status_code', None)
            ) from e
        except anthropic.NotFoundError as e:
            if "model" in str(e).lower():
                raise AIModelNotFoundError(
                    f"Model not found: {model}. Available models: {', '.join(self.available_models)}", 
                    provider="anthropic",
                    original_error=e,
                    status_code=getattr(e, 'status_code', None)
                ) from e
            else:
                raise AIProviderError(
                    f"Anthropic API error: {str(e)}", 
                    provider="anthropic",
                    original_error=e,
                    status_code=getattr(e, 'status_code', None)
                ) from e
        except anthropic.BadRequestError as e:
            raise AIProviderError(
                f"Anthropic bad request: {str(e)}", 
                provider="anthropic",
                original_error=e,
                status_code=getattr(e, 'status_code', None)
            ) from e
        except anthropic.APIError as e:
            raise AIProviderError(
                f"Anthropic API error: {str(e)}", 
                provider="anthropic",
                original_error=e,
                status_code=getattr(e, 'status_code', None)
            ) from e
        except Exception as e:
            raise AIProviderError(
                f"Unexpected error from Anthropic: {str(e)}", 
                provider="anthropic",
                original_error=e
            ) from e
    
    def _separate_system_message(
        self, messages: List[AIMessage]
    ) -> tuple[Optional[str], List[Dict[str, str]]]:
        """Separate system message from conversation messages.
        
        Anthropic API requires system prompt as a separate parameter,
        not as part of the messages array.
        
        Returns:
            Tuple of (system_prompt, conversation_messages)
        """
        system_prompt = None
        conversation_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                conversation_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        return system_prompt, conversation_messages
    
    def _extract_usage_info(self, response) -> Dict[str, Any]:
        """Extract usage information from Anthropic response"""
        if hasattr(response, 'usage'):
            return {
                "prompt_tokens": getattr(response.usage, 'input_tokens', 0),
                "completion_tokens": getattr(response.usage, 'output_tokens', 0),
                "total_tokens": getattr(response.usage, 'input_tokens', 0) + getattr(response.usage, 'output_tokens', 0)
            }
        return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
