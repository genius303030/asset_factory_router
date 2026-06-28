import unittest
import os
import json
import tempfile
from asset_factory.brief_loader import BriefLoader
from asset_factory.validator import BriefValidator

class TestBriefAndLoader(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.valid_brief_path = os.path.join(self.test_dir.name, "valid.json")
        with open(self.valid_brief_path, "w", encoding="utf-8") as f:
            json.dump({
                "project_name": "Test",
                "description": "A very detailed description of the project.",
                "target_outputs": ["mp4"],
                "style": "cyberpunk",
                "quality": "high",
                "budget": "high",
                "task_type": "video",
                "audience": "Gamers",
                "usage_context": "Ads"
            }, f)

        self.invalid_brief_path = os.path.join(self.test_dir.name, "invalid.json")
        with open(self.invalid_brief_path, "w", encoding="utf-8") as f:
            json.dump({
                "project_name": "Test"
            }, f)

    def tearDown(self):
        self.test_dir.cleanup()

    # 1. brief loader 正常讀取
    def test_brief_loader_success(self):
        brief = BriefLoader.load_from_file(self.valid_brief_path)
        self.assertEqual(brief.project_name, "Test")
        self.assertEqual(brief.task_type, "video")

    # 2. brief loader 缺欄位 (fallback defaults mapping)
    def test_brief_loader_missing_fields(self):
        brief = BriefLoader.load_from_file(self.invalid_brief_path)
        self.assertEqual(brief.project_name, "Test")
        self.assertEqual(brief.task_type, "image") # default from loader mapping

    # 3. brief validator valid case
    def test_validator_valid_case(self):
        res = BriefValidator.validate_file(self.valid_brief_path)
        self.assertEqual(res["status"], "valid")
        self.assertEqual(len(res["missing_fields"]), 0)

    # 4. brief validator missing fields
    def test_validator_missing_fields(self):
        res = BriefValidator.validate_file(self.invalid_brief_path)
        self.assertEqual(res["status"], "invalid")
        self.assertIn("description", res["missing_fields"])
        self.assertIn("target_outputs", res["missing_fields"])
