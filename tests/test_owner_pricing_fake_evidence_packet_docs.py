import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKET_PATH = REPO_ROOT / "docs" / "OWNER_PRICING_FAKE_IMPLEMENTATION_EVIDENCE_PACKET.md"
G2_REVIEW_PATH = (
    REPO_ROOT / "docs" / "OWNER_PRICING_FAKE_IMPLEMENTATION_EVIDENCE_G2_REVIEW.md"
)
README_PATH = REPO_ROOT / "README.md"
SAFETY_SCRIPT_PATH = REPO_ROOT / "scripts" / "check_owner_pricing_safety.py"


def normalized_text(path):
    return " ".join(path.read_text(encoding="utf-8").split())


class OwnerPricingFakeEvidencePacketDocsTests(unittest.TestCase):
    def test_required_docs_exist(self):
        self.assertTrue(PACKET_PATH.is_file())
        self.assertTrue(G2_REVIEW_PATH.is_file())

    def test_packet_preserves_fake_only_boundary(self):
        text = normalized_text(PACKET_PATH)

        self.assertIn("fake-only evidence packet", text)
        self.assertIn("does not implement runtime behavior", text)
        self.assertIn("does not register a parser", text)
        self.assertIn("does not add CLI flags to code", text)
        self.assertIn("does not change safety gate code", text)
        self.assertIn("does not touch real owner data", text)

    def test_packet_covers_required_evidence_sections(self):
        text = PACKET_PATH.read_text(encoding="utf-8")

        required_headings = (
            "Required Fake Input Artifacts",
            "Required Fake Output Artifacts",
            "Required Fake Audit Artifacts",
            "Required Fake Owner Report Artifacts",
            "Required Fake Rollback Artifacts",
            "Required Checksum Evidence",
            "Required Metrics Evidence",
            "Required Fixture Registry Updates",
            "Required Golden Report Updates",
            "G2 Review Checklist",
            "G0 Approval Checklist",
            "No-Go Conditions",
        )
        for heading in required_headings:
            self.assertIn(heading, text)

    def test_new_docs_do_not_introduce_production_enable_flag_or_parser_code(self):
        production_enable_flag = "--" + "enable" + "-production-import"
        for path in (PACKET_PATH, G2_REVIEW_PATH):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn(production_enable_flag, text)
            self.assertNotIn("add_parser(", text)

    def test_g2_review_blocks_real_data_and_runtime_changes(self):
        text = normalized_text(G2_REVIEW_PATH)

        self.assertIn("Is every artifact fake?", text)
        self.assertIn("Runtime behavior changed: no", text)
        self.assertIn("Safety gate code changed: no", text)
        self.assertIn("Real owner data present: no", text)
        self.assertIn("G2 must block the packet", text)

    def test_active_safety_script_still_contains_core_checks(self):
        text = SAFETY_SCRIPT_PATH.read_text(encoding="utf-8")

        for marker in (
            "check_cli_help",
            "check_parser_registration",
            "check_tracked_owner_pricing_data",
            "check_ignored_paths",
            "check_safety_markers",
            "check_ci_workflow_wiring",
        ):
            self.assertIn(marker, text)

    def test_readme_links_to_fake_evidence_docs(self):
        text = README_PATH.read_text(encoding="utf-8")

        self.assertIn("docs/OWNER_PRICING_FAKE_IMPLEMENTATION_EVIDENCE_PACKET.md", text)
        self.assertIn("docs/OWNER_PRICING_FAKE_IMPLEMENTATION_EVIDENCE_G2_REVIEW.md", text)


if __name__ == "__main__":
    unittest.main()
