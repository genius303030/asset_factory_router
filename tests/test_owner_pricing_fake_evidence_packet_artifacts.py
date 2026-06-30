from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKET_DIR = REPO_ROOT / "examples" / "owner_pricing_fake_evidence_packet"
DOC_PATH = REPO_ROOT / "docs" / "OWNER_PRICING_FAKE_EVIDENCE_PACKET_ARTIFACTS.md"
README_PATH = REPO_ROOT / "README.md"
MAIN_PATH = REPO_ROOT / "src" / "asset_factory" / "main.py"
SAFETY_GATE_PATH = REPO_ROOT / "scripts" / "check_owner_pricing_safety.py"
GITATTRIBUTES_PATH = REPO_ROOT / ".gitattributes"

PACKET_ARTIFACTS = (
    "README.md",
    "input/fake_owner_pricing_final_application_input.csv",
    "output/fake_owner_pricing_final_application_output.json",
    "audit/fake_owner_pricing_audit_log.json",
    "owner_report/fake_owner_pricing_owner_report.md",
    "rollback/fake_owner_pricing_rollback_plan.md",
    "checksums/SHA256SUMS.txt",
    "metrics/fake_owner_pricing_metrics_summary.json",
    "fixtures/fake_fixture_registry.json",
    "golden/fake_owner_pricing_golden_report.md",
)

CHECKSUM_ARTIFACTS = tuple(
    path for path in PACKET_ARTIFACTS if path != "checksums/SHA256SUMS.txt"
)

FAKE_IDENTIFIERS = (
    "FAKE_OWNER_ALPHA",
    "FAKE_JOB_001",
    "FAKE_MATERIAL_TEST_A",
    "FAKE_VENDOR_TEST",
)


def read_packet_text(relative_path: str) -> str:
    return (PACKET_DIR / relative_path).read_text(encoding="utf-8")


class OwnerPricingFakeEvidencePacketArtifactTests(unittest.TestCase):
    def test_all_packet_artifacts_exist_and_are_fake_only(self):
        for relative_path in PACKET_ARTIFACTS:
            artifact = PACKET_DIR / relative_path
            self.assertTrue(artifact.is_file(), relative_path)
            text = artifact.read_text(encoding="utf-8")
            self.assertIn("FAKE_ONLY", text, relative_path)
            self.assertNotIn(b"\r\n", artifact.read_bytes(), relative_path)

    def test_fake_identifiers_are_used_without_real_data_markers(self):
        combined_text = "\n".join(
            read_packet_text(relative_path) for relative_path in PACKET_ARTIFACTS
        )
        for identifier in FAKE_IDENTIFIERS:
            self.assertIn(identifier, combined_text)

        forbidden_fragments = (
            "OWNER_PRICING_PRIVATE",
            "CUSTOMER_PRIVATE",
            "PRIVATE_CUSTOMER",
            "PRODUCTION_CUSTOMER",
            "PRODUCTION_OWNER",
        )
        upper_text = combined_text.upper()
        for fragment in forbidden_fragments:
            self.assertNotIn(fragment, upper_text)

    def test_checksum_manifest_matches_packet_bytes(self):
        checksum_path = PACKET_DIR / "checksums" / "SHA256SUMS.txt"
        manifest: dict[str, str] = {}
        for line in checksum_path.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#"):
                continue
            digest, relative_path = line.split(maxsplit=1)
            manifest[relative_path] = digest

        expected_paths = {
            f"examples/owner_pricing_fake_evidence_packet/{path}"
            for path in CHECKSUM_ARTIFACTS
        }
        self.assertEqual(expected_paths, set(manifest))

        for relative_path, expected_digest in manifest.items():
            digest = hashlib.sha256((REPO_ROOT / relative_path).read_bytes()).hexdigest()
            self.assertEqual(expected_digest, digest, relative_path)

    def test_structured_artifacts_are_static_and_no_write(self):
        output = json.loads(
            read_packet_text("output/fake_owner_pricing_final_application_output.json")
        )
        audit = json.loads(read_packet_text("audit/fake_owner_pricing_audit_log.json"))
        metrics = json.loads(
            read_packet_text("metrics/fake_owner_pricing_metrics_summary.json")
        )
        registry = json.loads(read_packet_text("fixtures/fake_fixture_registry.json"))

        self.assertFalse(output["final_application_behavior_added"])
        self.assertFalse(output["live_json_mutated"])
        self.assertFalse(output["sandbox_json_mutated"])
        self.assertEqual(0, output["summary"]["fake_rows_written"])

        self.assertFalse(audit["final_application_behavior_added"])
        self.assertFalse(audit["parser_registration_added"])
        self.assertFalse(audit["safety_gate_changed"])

        flags = metrics["change_flags"]
        self.assertFalse(flags["src_changed"])
        self.assertFalse(flags["workflow_changed"])
        self.assertFalse(flags["production_behavior_changed"])
        self.assertFalse(flags["safety_gate_changed"])
        self.assertFalse(flags["live_json_mutated"])
        self.assertFalse(flags["sandbox_json_mutated"])

        boundary = registry["review_boundary"]
        self.assertFalse(boundary["runtime_behavior_added"])
        self.assertFalse(boundary["parser_registration_added"])
        self.assertFalse(boundary["formal_cli_flags_added"])
        self.assertFalse(boundary["real_data_allowed"])

    def test_golden_report_is_deterministic(self):
        golden = read_packet_text("golden/fake_owner_pricing_golden_report.md")
        self.assertIn("G1-037-FAKE-EVIDENCE-PACKET-V1", golden)
        self.assertIn("Fake output write count | 0", golden)
        self.assertIn("Production behavior changed | false", golden)
        self.assertNotRegex(golden.lower(), r"\b(now|today|generated at)\b")
        self.assertNotRegex(golden, r"[A-Z]:\\")

    def test_readme_docs_and_gitattributes_link_packet(self):
        readme = README_PATH.read_text(encoding="utf-8")
        doc = DOC_PATH.read_text(encoding="utf-8")
        packet_readme = read_packet_text("README.md")
        attributes = GITATTRIBUTES_PATH.read_text(encoding="utf-8")

        self.assertIn("docs/OWNER_PRICING_FAKE_EVIDENCE_PACKET_ARTIFACTS.md", readme)
        self.assertIn("examples/owner_pricing_fake_evidence_packet/", doc)
        self.assertIn("checksums/SHA256SUMS.txt", doc)
        self.assertIn("docs/OWNER_PRICING_FAKE_EVIDENCE_PACKET_ARTIFACTS.md", packet_readme)
        self.assertIn(
            "examples/owner_pricing_fake_evidence_packet/** text eol=lf",
            attributes,
        )

    def test_no_runtime_parser_flag_or_safety_gate_changes_are_required(self):
        main_source = MAIN_PATH.read_text(encoding="utf-8")
        safety_gate = SAFETY_GATE_PATH.read_text(encoding="utf-8")
        new_text = "\n".join(
            [DOC_PATH.read_text(encoding="utf-8")]
            + [read_packet_text(relative_path) for relative_path in PACKET_ARTIFACTS]
        )

        forbidden_command = "owner-pricing-" + "final-import"
        production_flag = "--" + "enable" + "-production-import"

        self.assertIsNone(
            re.search(r"add_parser\(\s*['\"]" + re.escape(forbidden_command) + r"['\"]", main_source)
        )
        self.assertNotIn(production_flag, main_source)
        self.assertNotIn(production_flag, new_text)

        self.assertIn("check_parser_registration", safety_gate)
        self.assertIn("check_tracked_owner_pricing_data", safety_gate)
        self.assertIn("check_ci_workflow_wiring", safety_gate)
        self.assertNotIn("owner_pricing_fake_evidence_packet", safety_gate)


if __name__ == "__main__":
    unittest.main()
