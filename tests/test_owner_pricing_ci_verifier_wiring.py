import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "python-ci.yml"
README_PATH = REPO_ROOT / "README.md"
WIRING_DOC_PATH = REPO_ROOT / "docs" / "OWNER_PRICING_CI_VERIFIER_WIRING.md"
VERIFIER_DOC_PATH = REPO_ROOT / "docs" / "OWNER_PRICING_FAKE_EVIDENCE_PACKET_VERIFIER.md"


def workflow_text():
    return WORKFLOW_PATH.read_text(encoding="utf-8")


class OwnerPricingCiVerifierWiringTests(unittest.TestCase):
    def test_workflow_keeps_existing_validation_steps(self):
        text = workflow_text()

        self.assertIn('python-version: "3.12"', text)
        self.assertIn("python -m unittest discover tests", text)
        self.assertIn('python -m unittest discover tests -p "test_owner_pricing.py"', text)
        self.assertIn("python scripts/check_owner_pricing_safety.py", text)
        self.assertIn("ruff check .", text)

    def test_workflow_runs_metrics_and_fake_packet_verifier(self):
        text = workflow_text()

        self.assertIn("python scripts/collect_pr_metrics.py --validate --summary", text)
        self.assertIn("python scripts/verify_owner_pricing_fake_evidence_packet.py", text)

    def test_owner_pricing_validation_order_is_preserved(self):
        text = workflow_text()

        safety_index = text.index("python scripts/check_owner_pricing_safety.py")
        metrics_index = text.index("python scripts/collect_pr_metrics.py --validate --summary")
        verifier_index = text.index("python scripts/verify_owner_pricing_fake_evidence_packet.py")
        ruff_index = text.index("ruff check .")

        self.assertLess(safety_index, metrics_index)
        self.assertLess(metrics_index, verifier_index)
        self.assertLess(verifier_index, ruff_index)

    def test_workflow_does_not_add_forbidden_runtime_or_write_commands(self):
        text = workflow_text()
        final_import_command = "owner-pricing-" + "final-import"
        production_enable_flag = "--" + "enable" + "-production-import"
        parser_call = "add_" + "parser("

        self.assertNotIn(final_import_command, text)
        self.assertNotIn(production_enable_flag, text)
        self.assertNotIn(parser_call, text)
        self.assertNotIn("owner-pricing-apply-sandbox-output", text)
        self.assertNotIn("live_json_mutated", text)
        self.assertNotIn("sandbox_json_mutated", text)

    def test_readme_and_docs_describe_ci_wiring(self):
        readme = README_PATH.read_text(encoding="utf-8")
        wiring_doc = WIRING_DOC_PATH.read_text(encoding="utf-8")
        verifier_doc = VERIFIER_DOC_PATH.read_text(encoding="utf-8")

        self.assertIn("docs/OWNER_PRICING_CI_VERIFIER_WIRING.md", readme)
        self.assertIn("python scripts/verify_owner_pricing_fake_evidence_packet.py", readme)
        self.assertIn("python scripts/verify_owner_pricing_fake_evidence_packet.py", wiring_doc)
        self.assertIn("CI Wiring", verifier_doc)
        self.assertIn("python scripts/verify_owner_pricing_fake_evidence_packet.py", verifier_doc)


if __name__ == "__main__":
    unittest.main()
