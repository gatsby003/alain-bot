"""
Factory for creating AI provider instances
"""

from typing import Optional, Dict, Any
from .base import AIProvider
from .config import AIClientConfig, ProviderType, ProviderConfig
from .anthropic import AnthropicProvider


class AIClientFactory:
    """Factory for creating and managing AI provider instances"""
    
    def __init__(self, config: Optional[AIClientConfig] = None):
        """Initialize with configuration"""
        self.config = config or AIClientConfig.from_env()
        self._provider_cache: Dict[ProviderType, AIProvider] = {}
    
    def create_provider(
        self, 
        provider_type: Optional[ProviderType] = None,
        **override_config
    ) -> AIProvider:
        """Create an AI provider instance
        
        Args:
            provider_type: Type of provider to create. If None, uses default.
            **override_config: Configuration overrides for the provider
            
        Returns:
            AIProvider instance
            
        Raises:
            ValueError: If provider type is not supported or configured
        """
        provider = provider_type or self.config.default_provider
        
        # Check cache first
        cache_key = provider
        if cache_key in self._provider_cache and not override_config:
            return self._provider_cache[cache_key]
        
        # Get provider configuration
        provider_config = self.config.get_provider_config(provider)
        
        # Merge override config
        final_config = {**provider_config.extra_config, **override_config}
        
        # Create provider instance
        instance = self._create_provider_instance(provider, provider_config, final_config)
        
        # Cache if no overrides were used
        if not override_config:
            self._provider_cache[cache_key] = instance
            
        return instance
    
    def _create_provider_instance(
        self, 
        provider_type: ProviderType, 
        config: ProviderConfig,
        extra_config: Dict[str, Any]
    ) -> AIProvider:
        """Create the actual provider instance"""
        if provider_type == ProviderType.ANTHROPIC:
            return AnthropicProvider(
                api_key=config.api_key,
                default_model=config.default_model,
                **extra_config
            )
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")
    
    def get_default_provider(self) -> AIProvider:
        """Get the default configured provider"""
        return self.create_provider()
    
    def clear_cache(self) -> None:
        """Clear the provider cache"""
        self._provider_cache.clear()
    
    @classmethod
    def create_quick(cls, provider: str = "anthropic", **config) -> AIProvider:
        """Quick factory method for creating a provider without full configuration
        
        Args:
            provider: Provider name (e.g., "anthropic")
            **config: Direct configuration options
            
        Returns:
            AIProvider instance
        """
        provider_type = ProviderType(provider.lower())
        
        if provider_type == ProviderType.ANTHROPIC:
            return AnthropicProvider(**config)
        else:
            raise ValueError(f"Unsupported provider: {provider}")


# Convenience function for simple usage
def create_ai_client(provider: str = "anthropic", **config) -> AIProvider:
    """Convenience function to create an AI client
    
    Args:
        provider: Provider name (default: "anthropic")
        **config: Provider-specific configuration
        
    Returns:
        AIProvider instance
    """
    return AIClientFactory.create_quick(provider, **config)