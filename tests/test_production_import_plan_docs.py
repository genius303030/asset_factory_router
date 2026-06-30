import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = REPO_ROOT / "docs" / "OWNER_PRICING_PRODUCTION_IMPORT_IMPLEMENTATION_PLAN_V2.md"
G0_PATH = REPO_ROOT / "docs" / "OWNER_PRICING_PRODUCTION_IMPORT_G0_APPROVAL_CHECKLIST.md"
G2_PATH = REPO_ROOT / "docs" / "OWNER_PRICING_PRODUCTION_IMPORT_G2_REVIEW_CHECKLIST.md"
README_PATH = REPO_ROOT / "README.md"


class ProductionImportPlanDocsTests(unittest.TestCase):
    def test_required_docs_exist(self):
        self.assertTrue(PLAN_PATH.is_file())
        self.assertTrue(G0_PATH.is_file())
        self.assertTrue(G2_PATH.is_file())

    def test_plan_preserves_planning_only_boundary(self):
        text = PLAN_PATH.read_text(encoding="utf-8")

        self.assertIn("planning-only", text)
        self.assertIn("does not implement production import", text)
        self.assertIn("does not add CLI", text)
        self.assertIn("Production import remains blocked", text)

    def test_new_docs_do_not_introduce_production_enable_flag(self):
        production_enable_flag = "--" + "enable" + "-production-import"
        for path in (PLAN_PATH, G0_PATH, G2_PATH):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn(production_enable_flag, text)
            self.assertNotIn("add_parser(", text)

    def test_checklists_define_review_and_approval_gates(self):
        g0_text = G0_PATH.read_text(encoding="utf-8")
        g2_text = G2_PATH.read_text(encoding="utf-8")

        self.assertIn("Required Approval Packet", g0_text)
        self.assertIn("Approval Stop Conditions", g0_text)
        self.assertIn("G1-033 Review Checklist", g2_text)
        self.assertIn("Future Implementation Review Checklist", g2_text)

    def test_readme_links_to_plan_v2(self):
        readme_text = README_PATH.read_text(encoding="utf-8")

        self.assertIn("docs/OWNER_PRICING_PRODUCTION_IMPORT_IMPLEMENTATION_PLAN_V2.md", readme_text)
        self.assertIn("docs/OWNER_PRICING_PRODUCTION_IMPORT_G0_APPROVAL_CHECKLIST.md", readme_text)
        self.assertIn("docs/OWNER_PRICING_PRODUCTION_IMPORT_G2_REVIEW_CHECKLIST.md", readme_text)


if __name__ == "__main__":
    unittest.main()
