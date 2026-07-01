import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DOC = REPO_ROOT / "docs" / "AUTO_WORKFLOW_OWNER_BRIEFING_TEMPLATE.md"
QUEUE_MAP_DOC = REPO_ROOT / "docs" / "G0_G1_G2_TASK_QUEUE_MAP.md"
BRIEFING_EXAMPLE = (
    REPO_ROOT / "examples" / "auto_workflow" / "owner_briefing.example.md"
)
SOURCE_EXAMPLE = (
    REPO_ROOT / "examples" / "auto_workflow" / "owner_briefing.source.example.json"
)
README = REPO_ROOT / "README.md"

REQUIRED_SOURCE_FIELDS = {
    "generated_at",
    "repo",
    "open_prs",
    "active_tasks",
    "waiting_review",
    "blocked_items",
    "next_actions",
    "owner_manual_action_required",
}

REQUIRED_TEMPLATE_SECTIONS = (
    "Today's Conclusion",
    "PR Status",
    "Task Status",
    "G1/G2 Division Of Work",
    "Blocked Items",
    "Next Action",
    "Owner Manual Action Required",
)


class AutoWorkflowOwnerBriefingDocsTests(unittest.TestCase):
    def test_required_files_exist(self):
        for path in (TEMPLATE_DOC, BRIEFING_EXAMPLE, SOURCE_EXAMPLE):
            self.assertTrue(path.is_file(), str(path))

    def test_template_doc_contains_required_sections_and_boundaries(self):
        template = TEMPLATE_DOC.read_text(encoding="utf-8")

        for section in REQUIRED_TEMPLATE_SECTIONS:
            self.assertIn(section, template)

        required_phrases = (
            "read-only",
            "No GitHub collector",
            "No token flow",
            "No automatic merge",
            "No owner-pricing runtime changes",
            "No live JSON mutation",
            "No sandbox JSON mutation",
        )
        for phrase in required_phrases:
            self.assertIn(phrase, template)

    def test_source_example_has_required_fields_and_safe_flags(self):
        source = json.loads(SOURCE_EXAMPLE.read_text(encoding="utf-8"))

        self.assertTrue(REQUIRED_SOURCE_FIELDS.issubset(source))
        self.assertIsInstance(source["open_prs"], list)
        self.assertIsInstance(source["active_tasks"], list)
        self.assertIsInstance(source["waiting_review"], list)
        self.assertIsInstance(source["blocked_items"], list)
        self.assertIsInstance(source["next_actions"], list)

        manual_action = source["owner_manual_action_required"]
        self.assertIn("required", manual_action)
        self.assertIn("reason", manual_action)
        self.assertIsInstance(manual_action["required"], bool)

        safety = source["safety_boundary"]
        self.assertTrue(safety["example_only"])
        self.assertTrue(safety["read_only"])
        self.assertFalse(safety["live_sync"])
        self.assertFalse(safety["github_api_used"])
        self.assertFalse(safety["token_required"])
        self.assertFalse(safety["external_api_calls_allowed"])
        self.assertFalse(safety["auto_merge_allowed"])
        self.assertFalse(safety["production_behavior_allowed"])
        self.assertFalse(safety["owner_pricing_runtime_change_allowed"])
        self.assertFalse(safety["live_json_mutation_allowed"])
        self.assertFalse(safety["sandbox_json_mutation_allowed"])

    def test_example_markdown_contains_required_sections_and_safety_words(self):
        briefing = BRIEFING_EXAMPLE.read_text(encoding="utf-8")
        briefing_lower = briefing.lower()

        for section in REQUIRED_TEMPLATE_SECTIONS:
            self.assertIn(section, briefing)

        for phrase in ("example-only", "read-only", "no auto-merge"):
            self.assertIn(phrase, briefing_lower)

        self.assertIn("not live sync", briefing_lower)
        self.assertIn("does not merge automatically", briefing_lower)

    def test_queue_map_and_readme_link_owner_briefing(self):
        queue_map = QUEUE_MAP_DOC.read_text(encoding="utf-8")
        readme = README.read_text(encoding="utf-8")

        self.assertIn("Owner Briefing In The Workflow", queue_map)
        self.assertIn("G1 produces briefing source data", queue_map)
        self.assertIn("G2 reviews the briefing", queue_map)
        self.assertIn("G0 makes the decision", queue_map)
        self.assertIn("must not auto-merge", queue_map)

        self.assertIn("docs/AUTO_WORKFLOW_OWNER_BRIEFING_TEMPLATE.md", readme)
        self.assertIn("examples/auto_workflow/owner_briefing.example.md", readme)
        self.assertIn(
            "examples/auto_workflow/owner_briefing.source.example.json",
            readme,
        )


if __name__ == "__main__":
    unittest.main()
