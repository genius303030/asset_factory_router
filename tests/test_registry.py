import unittest
from asset_factory.providers.registry import ProviderRegistry
from asset_factory.providers.base import ProviderProfile

class TestProviderRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = ProviderRegistry()

    # 10. provider registry loads providers
    def test_registry_loads_providers(self):
        providers = self.registry.list_all()
        self.assertTrue(len(providers) > 0)

    # 11. provider list contains expected providers
    def test_registry_contains_expected(self):
        names = [p.name for p in self.registry.list_all()]
        self.assertIn("OpenAI", names)
        self.assertIn("Runway", names)
        self.assertIn("Veo", names)
        self.assertIn("Fal.ai", names)
        self.assertIn("Leonardo.ai", names)
        self.assertIn("MockProvider", names)
