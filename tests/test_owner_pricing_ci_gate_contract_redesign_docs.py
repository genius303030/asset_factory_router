import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = REPO_ROOT / "docs" / "OWNER_PRICING_CI_GATE_CONTRACT_REDESIGN_PLAN.md"
G2_REVIEW_PATH = (
    REPO_ROOT / "docs" / "OWNER_PRICING_CI_GATE_CONTRACT_REDESIGN_G2_REVIEW.md"
)
README_PATH = REPO_ROOT / "README.md"
SAFETY_SCRIPT_PATH = REPO_ROOT / "scripts" / "check_owner_pricing_safety.py"


def normalized_text(path):
    return " ".join(path.read_text(encoding="utf-8").split())


class OwnerPricingCiGateContractRedesignDocsTests(unittest.TestCase):
    def test_required_docs_exist(self):
        self.assertTrue(PLAN_PATH.is_file())
        self.assertTrue(G2_REVIEW_PATH.is_file())

    def test_docs_preserve_planning_only_boundary(self):
        required_phrases = (
            "planning/docs/test-contract only",
            "does not change the active safety gate",
            "does not add parser registration",
            "does not add CLI flags",
            "does not change owner-pricing runtime behavior",
            "does not touch live JSON or sandbox JSON",
            "does not add real owner, customer, job, material, vendor, or pricing data",
        )
        for path in (PLAN_PATH, G2_REVIEW_PATH):
            text = normalized_text(path)
            for phrase in required_phrases:
                self.assertIn(phrase, text)

    def test_docs_name_current_and_future_gate_modes(self):
        for path in (PLAN_PATH, G2_REVIEW_PATH):
            text = path.read_text(encoding="utf-8")
            self.assertIn("reserved-command-absent", text)
            self.assertIn("approved-command-contract", text)

    def test_plan_contains_migration_criteria_and_no_go_conditions(self):
        text = PLAN_PATH.read_text(encoding="utf-8")

        self.assertIn("Migration Criteria", text)
        self.assertIn("No-Go Conditions", text)
        for phrase in (
            "G0 approval",
            "G2 review",
            "Fake fixtures",
            "Golden reports",
            "Metrics updates",
            "CI validates",
        ):
            self.assertIn(phrase, text)

    def test_g2_review_requires_existing_checks_to_remain(self):
        text = G2_REVIEW_PATH.read_text(encoding="utf-8")

        self.assertIn("Existing Checks Must Not Disappear", text)
        self.assertIn("Existing checks must not disappear", text)
        self.assertIn("No-Go Conditions", text)

    def test_active_safety_script_still_contains_core_check_markers(self):
        text = SAFETY_SCRIPT_PATH.read_text(encoding="utf-8")

        for marker in (
            "check_cli_help",
            "check_parser_registration",
            "check_production_flag_scope",
            "check_tracked_owner_pricing_data",
            "check_ignored_paths",
            "check_safety_markers",
            "check_ci_workflow_wiring",
        ):
            self.assertIn(marker, text)

    def test_new_docs_do_not_add_forbidden_runtime_strings(self):
        production_enable_flag = "--" + "enable" + "-production-import"
        parser_call = "add_" + "parser("
        for path in (PLAN_PATH, G2_REVIEW_PATH):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn(production_enable_flag, text)
            self.assertNotIn(parser_call, text)

    def test_readme_links_to_recovered_docs(self):
        text = README_PATH.read_text(encoding="utf-8")

        self.assertIn("docs/OWNER_PRICING_CI_GATE_CONTRACT_REDESIGN_PLAN.md", text)
        self.assertIn("docs/OWNER_PRICING_CI_GATE_CONTRACT_REDESIGN_G2_REVIEW.md", text)


if __name__ == "__main__":
    unittest.main()
