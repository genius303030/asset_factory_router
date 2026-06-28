import unittest
import os
import json
import tempfile
import subprocess
from asset_factory.models import AssetPack, ProjectBrief, RoutingPlan
from asset_factory.asset_pack_writer import AssetPackWriter

class TestWriterAndCLI(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    # 14. asset writer creates required files
    def test_writer_creates_required_files(self):
        out_dir = os.path.join(self.test_dir.name, "pack1")
        brief = ProjectBrief("Test", "image", "generic", "medium", "normal", "medium", "medium", "Desc", "Aud")
        plan = RoutingPlan("A", "B", {}, {}, "Reason", "Risk", "2", "3", "config")
        manifest = {"project": "Test"}
        
        pack = AssetPack(
            project_brief=brief,
            prompt_pack_md="Content",
            image_prompts=[{"primary": "Prompt"}],
            ui_style_guide_md="UI",
            storyboard_md="Story",
            asset_manifest=manifest,
            routing_plan=plan,
            codex_task_md="Codex",
            production_checklist_md="Checklist",
            pack_summary_md="Summary"
        )
        
        AssetPackWriter.write(pack, out_dir)
        
        files = os.listdir(out_dir)
        self.assertEqual(len(files), 10)
        self.assertIn("project_brief.json", files)
        self.assertIn("prompt_pack.md", files)
        self.assertIn("image_prompts.json", files)
        self.assertIn("ui_style_guide.md", files)
        self.assertIn("storyboard.md", files)
        self.assertIn("asset_manifest.json", files)
        self.assertIn("routing_plan.json", files)
        self.assertIn("codex_asset_tasks.md", files)
        self.assertIn("production_checklist.md", files)
        self.assertIn("pack_summary.md", files)

        # 19. routing_plan JSON parseable
        with open(os.path.join(out_dir, "routing_plan.json")) as f:
            data = json.load(f)
            self.assertEqual(data["recommended_provider"], "A")

        # 20. asset_manifest JSON parseable
        with open(os.path.join(out_dir, "asset_manifest.json")) as f:
            data = json.load(f)
            self.assertEqual(data["project"], "Test")

    # Smoke tests via CLI 
    # 15. create command smoke test
    # 16. route command smoke test
    # 17. validate command smoke test
    # 18. inspect command smoke test
    def test_cli_smoke_tests(self):
        # Create dummy brief
        brief_path = os.path.join(self.test_dir.name, "brief.json")
        with open(brief_path, "w", encoding="utf-8") as f:
            json.dump({
                "project_name": "Test",
                "description": "Desc",
                "target_outputs": ["png"],
                "style": "cyberpunk",
                "quality": "high",
                "budget": "high",
                "task_type": "image",
                "audience": "Gamers",
                "usage_context": "Ads"
            }, f)
            
        out_dir = os.path.join(self.test_dir.name, "outpack")

        # Validate
        res = subprocess.run(["asset-factory", "validate", "--brief", brief_path], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        
        # Create
        res = subprocess.run(["asset-factory", "create", "--brief", brief_path, "--out", out_dir], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertTrue(os.path.exists(out_dir))

        # Inspect
        res = subprocess.run(["asset-factory", "inspect", "--pack", out_dir], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("Ready", res.stdout)

        # Route
        res = subprocess.run(["asset-factory", "route", "--task", "image", "--style", "cyberpunk"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
