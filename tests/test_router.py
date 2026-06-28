import unittest
from asset_factory.router import ModelRouter
from asset_factory.providers.registry import ProviderRegistry
from asset_factory.providers.base import ProviderProfile
from asset_factory.scoring import ConfiguredScoringSystem

class TestRouter(unittest.TestCase):
    def setUp(self):
        self.registry = ProviderRegistry()

    # 5. router quality priority
    def test_router_quality_priority(self):
        plan = ModelRouter.generate_routing_plan("video", "realistic", "ultra", "slow", "high")
        # Veo has highest quality (5) for video. With slow speed and high budget, Veo should win.
        self.assertEqual(plan.recommended_provider, "Veo")

    # 6. router speed priority
    def test_router_speed_priority(self):
        plan = ModelRouter.generate_routing_plan("image", "generic", "medium", "fast", "medium")
        # Fal.ai is the fastest (5) for image
        self.assertEqual(plan.recommended_provider, "Fal.ai")

    # 7. router budget priority
    def test_router_budget_priority(self):
        plan = ModelRouter.generate_routing_plan("ui", "generic", "medium", "normal", "low")
        self.assertEqual(plan.recommended_provider, "Leonardo.ai")

    # 8. router unsupported task elimination
    def test_router_unsupported_task(self):
        plan = ModelRouter.generate_routing_plan("audio", "generic", "medium", "normal", "medium")
        # MockProvider is ignored unless it's the only one. So it should return None.
        self.assertEqual(plan.recommended_provider, "None")

    # 9. router config changes result
    def test_router_config_change(self):
        # We manually inject a config
        custom_config = {
            "quality_weight": { "medium": 0.0 },
            "speed_weight": { "normal": 0.0 },
            "budget_weight": { "medium": 0.0 },
            "style_bonus": 0.0,
            "provider_penalty": {"OpenAI": -100.0}
        }
        brief_data = {"task_type": "image"}
        score, _ = ConfiguredScoringSystem.calculate_score(self.registry.get("OpenAI"), brief_data, custom_config)
        self.assertLess(score, 0) # penalized
