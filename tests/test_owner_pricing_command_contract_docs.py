import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "docs" / "OWNER_PRICING_COMMAND_CONTRACT.md"
MATRIX_PATH = REPO_ROOT / "docs" / "OWNER_PRICING_TEST_MATRIX.md"
G2_REVIEW_PATH = REPO_ROOT / "docs" / "OWNER_PRICING_COMMAND_CONTRACT_G2_REVIEW.md"
README_PATH = REPO_ROOT / "README.md"
SOURCE_PATHS = (
    REPO_ROOT / "src" / "asset_factory" / "main.py",
    REPO_ROOT / "src" / "asset_factory" / "owner_pricing.py",
)


class OwnerPricingCommandContractDocsTests(unittest.TestCase):
    def test_required_docs_exist(self):
        self.assertTrue(CONTRACT_PATH.is_file())
        self.assertTrue(MATRIX_PATH.is_file())
        self.assertTrue(G2_REVIEW_PATH.is_file())

    def test_contract_preserves_design_only_boundary(self):
        text = CONTRACT_PATH.read_text(encoding="utf-8")

        self.assertIn("design-only command contract", text)
        self.assertIn("does not register a", text)
        self.assertIn("does not add command-line flags to code", text)
        self.assertIn("does not change runtime", text)
        self.assertIn("asset-factory owner-pricing-final-import", text)

    def test_new_docs_do_not_restate_production_enable_flag_or_parser_code(self):
        production_enable_flag = "--" + "enable" + "-production-import"
        for path in (CONTRACT_PATH, MATRIX_PATH, G2_REVIEW_PATH):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn(production_enable_flag, text)
            self.assertNotIn("add_parser(", text)

    def test_test_matrix_contains_required_fail_closed_cases(self):
        text = MATRIX_PATH.read_text(encoding="utf-8")

        for case_id in ("OP-FI-001", "OP-FI-020", "OP-FI-029", "OP-FI-040"):
            self.assertIn(case_id, text)
        self.assertIn("Production Write", text)
        self.assertIn("Safety gate fails", text)

    def test_g2_review_defines_no_go_findings(self):
        text = G2_REVIEW_PATH.read_text(encoding="utf-8")

        self.assertIn("G1-034 Review Checklist", text)
        self.assertIn("Future Implementation Review Checklist", text)
        self.assertIn("No-Go Review Findings", text)

    def test_readme_links_to_command_contract_docs(self):
        text = README_PATH.read_text(encoding="utf-8")

        self.assertIn("docs/OWNER_PRICING_COMMAND_CONTRACT.md", text)
        self.assertIn("docs/OWNER_PRICING_TEST_MATRIX.md", text)
        self.assertIn("docs/OWNER_PRICING_COMMAND_CONTRACT_G2_REVIEW.md", text)

    def test_runtime_sources_do_not_register_reserved_command(self):
        forbidden_parser = "add_parser(" + repr("owner-pricing-final-import")
        for path in SOURCE_PATHS:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn(forbidden_parser, text)


if __name__ == "__main__":
    unittest.main()
