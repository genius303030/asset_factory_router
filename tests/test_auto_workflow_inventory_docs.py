import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AUTO_WORKFLOW_DOC = REPO_ROOT / "docs" / "AUTO_WORKFLOW_INVENTORY.md"
TASK_QUEUE_MAP_DOC = REPO_ROOT / "docs" / "G0_G1_G2_TASK_QUEUE_MAP.md"
TASK_QUEUE_EXAMPLE = (
    REPO_ROOT / "examples" / "auto_workflow" / "task_queue.example.json"
)
README = REPO_ROOT / "README.md"

REQUIRED_QUEUE_FIELDS = {
    "task_id",
    "title",
    "repo",
    "owner",
    "status",
    "priority",
    "next_action",
    "blocked_reason",
    "review_required",
    "source_pr",
    "source_issue",
    "updated_at",
}

ALLOWED_STATUS_VALUES = {
    "candidate",
    "ready_for_g1",
    "in_progress",
    "blocked",
    "needs_g2_review",
    "needs_g0_decision",
    "done",
    "closed",
}


class AutoWorkflowInventoryDocsTests(unittest.TestCase):
    def test_inventory_doc_exists_and_names_current_gaps(self):
        inventory = AUTO_WORKFLOW_DOC.read_text(encoding="utf-8")

        required_phrases = (
            "# Auto Workflow Inventory",
            "Current Auto Workflow Surfaces",
            "What Is Missing For Auto Workflow",
            "G0 Readiness Summary",
            "No GitHub API token",
            "No external API calls from tests",
            "owner briefing",
        )
        for phrase in required_phrases:
            self.assertIn(phrase, inventory)

    def test_task_queue_map_exists_and_defines_review_flow(self):
        queue_map = TASK_QUEUE_MAP_DOC.read_text(encoding="utf-8")

        required_phrases = (
            "# G0/G1/G2 Task Queue Map",
            "Required fields",
            "Suggested Status Values",
            "Routing Rules",
            "Review Required Rule",
            "Owner Briefing Shape",
        )
        for phrase in required_phrases:
            self.assertIn(phrase, queue_map)

        for field in REQUIRED_QUEUE_FIELDS:
            self.assertIn(f"`{field}`", queue_map)

    def test_task_queue_example_has_required_fields(self):
        task = json.loads(TASK_QUEUE_EXAMPLE.read_text(encoding="utf-8"))

        self.assertTrue(REQUIRED_QUEUE_FIELDS.issubset(task))
        self.assertEqual("G1-040", task["task_id"])
        self.assertIn(task["status"], ALLOWED_STATUS_VALUES)
        self.assertIsInstance(task["review_required"], bool)
        self.assertIsInstance(task["next_action"], str)
        self.assertNotEqual("", task["next_action"].strip())
        self.assertIsNone(task["source_pr"])
        self.assertIsNone(task["source_issue"])
        self.assertTrue(task["updated_at"].endswith("+08:00"))

    def test_task_queue_example_preserves_safety_boundary(self):
        task = json.loads(TASK_QUEUE_EXAMPLE.read_text(encoding="utf-8"))
        safety_boundary = task["safety_boundary"]

        self.assertTrue(safety_boundary["read_only"])
        self.assertFalse(safety_boundary["github_api_token_required"])
        self.assertFalse(safety_boundary["external_api_calls_allowed"])
        self.assertFalse(safety_boundary["private_data_allowed"])
        self.assertFalse(safety_boundary["owner_pricing_runtime_change_allowed"])
        self.assertFalse(safety_boundary["live_json_mutation_allowed"])
        self.assertFalse(safety_boundary["sandbox_json_mutation_allowed"])

    def test_readme_links_auto_workflow_inventory(self):
        readme = README.read_text(encoding="utf-8")

        self.assertIn("## Auto Workflow Inventory", readme)
        self.assertIn("docs/AUTO_WORKFLOW_INVENTORY.md", readme)
        self.assertIn("docs/G0_G1_G2_TASK_QUEUE_MAP.md", readme)
        self.assertIn("examples/auto_workflow/task_queue.example.json", readme)


if __name__ == "__main__":
    unittest.main()
