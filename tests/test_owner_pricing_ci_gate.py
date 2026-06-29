import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_owner_pricing_safety.py"
SPEC = importlib.util.spec_from_file_location("check_owner_pricing_safety", SCRIPT_PATH)
owner_pricing_gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(owner_pricing_gate)


class OwnerPricingCiGateTests(unittest.TestCase):
    def test_final_import_command_regex_allows_safe_suffixes(self):
        stem = owner_pricing_gate.FINAL_IMPORT_COMMAND

        self.assertTrue(owner_pricing_gate.contains_forbidden_command(f"asset-factory {stem}"))
        self.assertTrue(owner_pricing_gate.contains_forbidden_command(f"{stem},"))
        self.assertFalse(owner_pricing_gate.contains_forbidden_command(f"{stem}-preflight"))
        self.assertFalse(owner_pricing_gate.contains_forbidden_command(f"{stem}-fake-rehearsal"))

    def test_future_flag_allowlist_is_limited_to_planning_docs(self):
        self.assertFalse(
            owner_pricing_gate.is_forbidden_flag_path(
                "docs/OWNER_PRICING_FINAL_IMPORT_PLAN.md"
            )
        )
        self.assertTrue(owner_pricing_gate.is_forbidden_flag_path("README.md"))
        self.assertTrue(owner_pricing_gate.is_forbidden_flag_path("src/asset_factory/main.py"))

    def test_real_owner_pricing_data_detection_allows_fake_examples(self):
        self.assertIsNone(
            owner_pricing_gate.real_owner_pricing_data_reason(
                "examples/owner_pricing/fake_owner_pricing.csv"
            )
        )
        self.assertIsNotNone(
            owner_pricing_gate.real_owner_pricing_data_reason(
                "owner_pricing_private/real_owner_pricing.csv"
            )
        )
        self.assertIsNotNone(
            owner_pricing_gate.real_owner_pricing_data_reason(
                "input/owner_pricing/private/real_owner_pricing.csv"
            )
        )
        self.assertIsNotNone(
            owner_pricing_gate.real_owner_pricing_data_reason(
                "input/owner_pricing/customer_owner_pricing.csv"
            )
        )


if __name__ == "__main__":
    unittest.main()
