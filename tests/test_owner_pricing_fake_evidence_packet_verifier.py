from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "verify_owner_pricing_fake_evidence_packet.py"
PACKET_DIR = REPO_ROOT / "examples" / "owner_pricing_fake_evidence_packet"
DOC_PATH = REPO_ROOT / "docs" / "OWNER_PRICING_FAKE_EVIDENCE_PACKET_VERIFIER.md"
README_PATH = REPO_ROOT / "README.md"
MAIN_PATH = REPO_ROOT / "src" / "asset_factory" / "main.py"
SAFETY_GATE_PATH = REPO_ROOT / "scripts" / "check_owner_pricing_safety.py"


def load_verifier_module():
    spec = importlib.util.spec_from_file_location(
        "verify_owner_pricing_fake_evidence_packet",
        SCRIPT_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class OwnerPricingFakeEvidencePacketVerifierTests(unittest.TestCase):
    def setUp(self):
        self.verifier = load_verifier_module()

    def copy_packet(self, temp_dir: Path) -> Path:
        packet_copy = temp_dir / "owner_pricing_fake_evidence_packet"
        shutil.copytree(PACKET_DIR, packet_copy)
        return packet_copy

    def test_default_packet_success_path(self):
        errors = self.verifier.verify_packet()
        self.assertEqual([], errors)

        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT_PATH)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual("", result.stderr)
        self.assertEqual(0, result.returncode)
        self.assertIn("verification passed", result.stdout)

    def test_missing_file_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            packet_copy = self.copy_packet(Path(temp))
            missing = packet_copy / "golden" / "fake_owner_pricing_golden_report.md"
            missing.unlink()

            errors = self.verifier.verify_packet(packet_copy)

        self.assertTrue(any("missing required artifact" in error for error in errors))

    def test_missing_fake_only_marker_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            packet_copy = self.copy_packet(Path(temp))
            readme = packet_copy / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8").replace("FAKE_ONLY", "FAKE_MARKER_REMOVED"),
                encoding="utf-8",
            )

            errors = self.verifier.verify_packet(packet_copy)

        self.assertTrue(any("missing FAKE_ONLY marker" in error for error in errors))

    def test_checksum_mismatch_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            packet_copy = self.copy_packet(Path(temp))
            report = packet_copy / "owner_report" / "fake_owner_pricing_owner_report.md"
            report.write_text(
                report.read_text(encoding="utf-8") + "\nFAKE_ONLY checksum mismatch sample\n",
                encoding="utf-8",
            )

            errors = self.verifier.verify_packet(packet_copy)

        self.assertTrue(any("checksum mismatch" in error for error in errors))

    def test_docs_readme_and_safety_boundary_are_present(self):
        doc = DOC_PATH.read_text(encoding="utf-8")
        readme = README_PATH.read_text(encoding="utf-8")
        main_source = MAIN_PATH.read_text(encoding="utf-8")
        safety_gate = SAFETY_GATE_PATH.read_text(encoding="utf-8")

        production_flag = "--" + "enable" + "-production-import"
        forbidden_command = "owner-pricing-" + "final-import"

        self.assertIn("scripts/verify_owner_pricing_fake_evidence_packet.py", doc)
        self.assertIn("scripts/verify_owner_pricing_fake_evidence_packet.py", readme)
        self.assertNotIn(production_flag, doc)
        self.assertNotIn(production_flag, readme)
        self.assertNotIn(production_flag, main_source)
        self.assertNotIn("verify_owner_pricing_fake_evidence_packet", main_source)
        self.assertNotIn("verify_owner_pricing_fake_evidence_packet", safety_gate)
        self.assertNotIn(f'add_parser("{forbidden_command}"', main_source)


if __name__ == "__main__":
    unittest.main()
