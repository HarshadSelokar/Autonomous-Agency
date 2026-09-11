"""
Model Provider Registry & Factory.
Decouples application runtime from specific provider concrete instances.
"""

from src.domain.exceptions import ConfigurationError
from src.domain.model_provider import ModelProviderInterface


class ModelProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, ModelProviderInterface] = {}

    def register(self, provider: ModelProviderInterface) -> None:
        """Register a provider instance by its provider_name."""
        self._providers[provider.provider_name.lower()] = provider

    def get(self, provider_name: str) -> ModelProviderInterface:
        """Get a registered provider by name, raising ConfigurationError if missing."""
        name = provider_name.lower()
        if name not in self._providers:
            raise ConfigurationError(
                f"Model provider '{provider_name}' is not registered. "
                f"Available providers: {list(self._providers.keys())}"
            )
        return self._providers[name]

    def has(self, provider_name: str) -> bool:
        """Check if provider_name is registered."""
        return provider_name.lower() in self._providers


# Global default registry instance
default_provider_registry = ModelProviderRegistry()
