import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = REPO_ROOT / "docs" / "OWNER_PRICING_CI_GATE_CONTRACT_REDESIGN_PLAN.md"
G2_REVIEW_PATH = (
    REPO_ROOT / "docs" / "OWNER_PRICING_CI_GATE_CONTRACT_REDESIGN_G2_REVIEW.md"
)
README_PATH = REPO_ROOT / "README.md"
SAFETY_SCRIPT_PATH = REPO_ROOT / "scripts" / "check_owner_pricing_safety.py"


class OwnerPricingCiGateContractRedesignDocsTests(unittest.TestCase):
    def test_required_docs_exist(self):
        self.assertTrue(PLAN_PATH.is_file())
        self.assertTrue(G2_REVIEW_PATH.is_file())

    def test_plan_preserves_planning_only_boundary(self):
        text = PLAN_PATH.read_text(encoding="utf-8")

        self.assertIn("planning/docs/test-contract", text)
        self.assertIn("does not modify `scripts/check_owner_pricing_safety.py`", text)
        self.assertIn("does not add parser registration", text)
        self.assertIn("does not add CLI flags to code", text)
        self.assertIn("change runtime behavior", text)
        self.assertIn("remove\nexisting checks", text)

    def test_plan_documents_both_future_gate_modes(self):
        text = PLAN_PATH.read_text(encoding="utf-8")

        self.assertIn("Reserved-Command-Absent", text)
        self.assertIn("Approved-Command-Contract", text)
        self.assertIn("Migration Criteria", text)
        self.assertIn("No-Go Conditions", text)

    def test_new_docs_do_not_introduce_production_enable_flag_or_parser_code(self):
        production_enable_flag = "--" + "enable" + "-production-import"
        for path in (PLAN_PATH, G2_REVIEW_PATH):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn(production_enable_flag, text)
            self.assertNotIn("add_parser(", text)

    def test_review_doc_lists_existing_checks_that_must_not_disappear(self):
        text = G2_REVIEW_PATH.read_text(encoding="utf-8")

        self.assertIn("Existing Checks That Must Not Disappear", text)
        self.assertIn("Expected owner-pricing commands remain present", text)
        self.assertIn("Real owner-pricing data is not tracked", text)
        self.assertIn("CI workflow includes the safety gate", text)

    def test_active_safety_script_still_contains_current_core_checks(self):
        text = SAFETY_SCRIPT_PATH.read_text(encoding="utf-8")

        required_markers = (
            "check_cli_help",
            "check_parser_registration",
            "check_production_flag_scope",
            "check_tracked_owner_pricing_data",
            "check_ignored_paths",
            "check_safety_markers",
            "check_ci_workflow_wiring",
        )
        for marker in required_markers:
            self.assertIn(marker, text)

    def test_readme_links_to_redesign_docs(self):
        text = README_PATH.read_text(encoding="utf-8")

        self.assertIn("docs/OWNER_PRICING_CI_GATE_CONTRACT_REDESIGN_PLAN.md", text)
        self.assertIn("docs/OWNER_PRICING_CI_GATE_CONTRACT_REDESIGN_G2_REVIEW.md", text)


if __name__ == "__main__":
    unittest.main()
