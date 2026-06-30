from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = REPO_ROOT / "examples" / "owner_pricing"
REGISTRY_PATH = REPO_ROOT / "docs" / "OWNER_PRICING_FIXTURE_REGISTRY.md"
EXAMPLES_README_PATH = EXAMPLES_DIR / "README.md"
GOLDEN_POLICY_PATH = REPO_ROOT / "docs" / "OWNER_PRICING_GOLDEN_REPORTS.md"

CHECKSUM_SENSITIVE_FIXTURES = {
    "examples/owner_pricing/fake_current_pricing.csv",
    "examples/owner_pricing/fake_sandbox_pricing_output.json",
    "examples/owner_pricing/fake_owner_pricing_approval_record.json",
    "examples/owner_pricing/fake_final_import_preflight_report.json",
    "examples/owner_pricing/fake_final_import_rehearsal_production_target.csv",
    "examples/owner_pricing/fake_final_import_rehearsal_preflight_report.json",
    "examples/owner_pricing/fake_final_import_rehearsal_audit.json",
}


def _git_lines(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _tracked_fake_examples() -> list[str]:
    return [
        path
        for path in _git_lines("ls-files", "examples/owner_pricing")
        if Path(path).name.startswith("fake_")
    ]


class OwnerPricingFixtureRegistryTests(unittest.TestCase):
    def test_registry_lists_every_committed_owner_pricing_example(self):
        tracked_examples = _tracked_fake_examples()
        registry = REGISTRY_PATH.read_text(encoding="utf-8")

        self.assertIn("Path | Workflow stage | Artifact kind", registry)
        for path in tracked_examples:
            self.assertIn(f"`{path}`", registry)
            self.assertIn("| committed |", registry)

    def test_examples_readme_lists_every_committed_owner_pricing_example(self):
        tracked_examples = _tracked_fake_examples()
        readme = EXAMPLES_README_PATH.read_text(encoding="utf-8")

        for path in tracked_examples:
            name = Path(path).name
            self.assertIn(f"`{name}`", readme)

    def test_checksum_sensitive_fixtures_are_marked_and_lf_only(self):
        registry = REGISTRY_PATH.read_text(encoding="utf-8")
        for path in CHECKSUM_SENSITIVE_FIXTURES:
            self.assertIn(f"`{path}`", registry)
            registry_line = next(
                line for line in registry.splitlines() if f"`{path}`" in line
            )
            self.assertIn("checksum-sensitive", registry_line)
            self.assertIn("| yes |", registry_line)

            fixture_bytes = (REPO_ROOT / path).read_bytes()
            self.assertNotIn(b"\r\n", fixture_bytes)

    def test_gitattributes_preserves_lf_for_owner_pricing_examples(self):
        attributes = (REPO_ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn("examples/owner_pricing/* text eol=lf", attributes)

    def test_golden_policy_keeps_real_outputs_local(self):
        policy = GOLDEN_POLICY_PATH.read_text(encoding="utf-8")

        self.assertIn("Must remain local/ignored", policy)
        self.assertIn("No real owner pricing data was added.", policy)
        self.assertIn("No owner-pricing production behavior changed.", policy)
        self.assertIn(
            "No production final-import command or production-enable flag was added.",
            policy,
        )


if __name__ == "__main__":
    unittest.main()
