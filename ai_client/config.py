"""
Configuration management for AI client providers
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum


class ProviderType(Enum):
    """Supported AI providers"""
    ANTHROPIC = "anthropic"
    # Future providers can be added here
    # OPENAI = "openai"
    # GOOGLE = "google"


@dataclass
class ProviderConfig:
    """Configuration for a specific AI provider"""
    provider_type: ProviderType
    api_key: Optional[str] = None
    default_model: Optional[str] = None
    extra_config: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_env(cls, provider_type: ProviderType) -> "ProviderConfig":
        """Create provider config from environment variables"""
        if provider_type == ProviderType.ANTHROPIC:
            return cls(
                provider_type=provider_type,
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                default_model=os.getenv("ANTHROPIC_DEFAULT_MODEL", "claude-3-5-sonnet-20241022")
            )
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")


@dataclass
class AIClientConfig:
    """Main configuration for the AI client system"""
    default_provider: ProviderType = ProviderType.ANTHROPIC
    providers: Dict[ProviderType, ProviderConfig] = field(default_factory=dict)
    
    @classmethod
    def from_env(cls) -> "AIClientConfig":
        """Create configuration from environment variables"""
        config = cls()
        
        # Determine default provider from environment
        provider_name = os.getenv("AI_PROVIDER", "anthropic").lower()
        try:
            config.default_provider = ProviderType(provider_name)
        except ValueError:
            config.default_provider = ProviderType.ANTHROPIC
        
        # Load configuration for available providers
        if os.getenv("ANTHROPIC_API_KEY"):
            config.providers[ProviderType.ANTHROPIC] = ProviderConfig.from_env(ProviderType.ANTHROPIC)
        
        return config
    
    def get_provider_config(self, provider_type: Optional[ProviderType] = None) -> ProviderConfig:
        """Get configuration for a specific provider, defaulting to the default provider"""
        provider = provider_type or self.default_provider
        
        if provider not in self.providers:
            raise ValueError(f"Provider {provider.value} is not configured. Check your API keys.")
        
        return self.providers[provider]