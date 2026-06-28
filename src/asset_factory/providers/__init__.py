from .base import BaseProvider, ProviderProfile
from .registry import ProviderRegistry

def get_provider_by_name(name: str) -> BaseProvider:
    provider = ProviderRegistry.get(name)
    if not provider:
        from .mock_provider import MockProvider
        return MockProvider()
    return provider
