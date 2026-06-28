import unittest
from asset_factory.prompt_engine import PromptEngine
from asset_factory.models import RoutingPlan

class TestPromptEngine(unittest.TestCase):
    def setUp(self):
        self.engine = PromptEngine()
        self.brief_dict = {
            "project_name": "Test Project",
            "task_type": "image",
            "style": "anime",
            "quality": "high",
            "speed": "normal",
            "budget": "low",
            "description": "A cool anime picture",
            "target_outputs": ["png"]
        }
        self.routing_plan = RoutingPlan(
            recommended_provider="OpenAI",
            fallback_provider="MockProvider",
            all_provider_scores={},
            score_breakdown={},
            reason="Because.",
            risk_notes="None.",
            estimated_cost_level="2",
            estimated_speed_level="3",
            selected_config_source="default"
        )

    # 12. prompt engine creates prompt pack
    def test_creates_prompt_pack(self):
        pack = self.engine.generate_prompt_pack(self.brief_dict, self.routing_plan)
        self.assertIsInstance(pack, str)
        self.assertTrue(len(pack) > 100)

    # 13. prompt engine output has required sections
    def test_prompt_pack_has_required_sections(self):
        pack = self.engine.generate_prompt_pack(self.brief_dict, self.routing_plan)
        self.assertIn("## 1. Project Summary", pack)
        self.assertIn("## 2. Creative Direction", pack)
        self.assertIn("## 3. Visual Style Keywords", pack)
        self.assertIn("## 4. Image Prompt Set", pack)
        self.assertIn("## 5. UI / Asset Style Guide", pack)
        self.assertIn("## 6. Storyboard Draft", pack)
        self.assertIn("## 7. Model Routing Notes", pack)
        self.assertIn("## 8. Codex Implementation Notes", pack)
        self.assertIn("## 9. Negative Prompts / Avoid List", pack)
        self.assertIn("## 10. Asset Manifest Summary", pack)
        self.assertIn("## 11. Next Production Steps", pack)
