import os
import subprocess
import sys
import tempfile
import unittest

from asset_factory.owner_pricing import (
    dry_run_owner_pricing_import,
    write_preview_report,
)


OWNER_PRICING_SAMPLE = """material_key,material_name,unit,unit_price
sample_concrete,Demo Concrete,bags,125.50
sample_rebar,Demo Rebar,pcs,88
sample_sand,Demo Sand,m3,42.00
sample_rebar,Demo Rebar Duplicate,pcs,90
sample_missing_unit,Demo Missing Unit,,12.00
sample_bad_price,Demo Bad Price,kg,abc
sample_unchanged,Demo Unchanged,kg,30.00
"""


CURRENT_PRICING_SAMPLE = """material_key,material_name,unit,unit_price
sample_concrete,Demo Concrete,bags,120.00
sample_unchanged,Demo Unchanged,kg,30.00
sample_old_only,Demo Existing Only,liter,10.00
"""


class TestOwnerPricingDryRun(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.csv_path = os.path.join(self.test_dir.name, "owner_pricing.csv")
        self.current_path = os.path.join(self.test_dir.name, "current_pricing.csv")
        with open(self.csv_path, "w", encoding="utf-8") as file:
            file.write(OWNER_PRICING_SAMPLE)
        with open(self.current_path, "w", encoding="utf-8") as file:
            file.write(CURRENT_PRICING_SAMPLE)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_dry_run_validates_and_compares_owner_pricing_csv(self):
        result = dry_run_owner_pricing_import(self.csv_path, self.current_path)

        self.assertEqual(result.rows_read, 7)
        self.assertEqual(result.valid_rows, 3)
        self.assertEqual(result.invalid_rows, 4)
        self.assertEqual(result.current_records_read, 3)

        self.assertEqual(len(result.duplicate_material_keys), 1)
        self.assertEqual(result.duplicate_material_keys[0].material_key, "sample_rebar")
        self.assertEqual(result.duplicate_material_keys[0].rows, [3, 5])

        self.assertEqual(len(result.missing_required_fields), 1)
        self.assertEqual(result.missing_required_fields[0].row_number, 6)
        self.assertEqual(result.missing_required_fields[0].fields, ["unit"])

        self.assertEqual(len(result.price_format_issues), 1)
        self.assertEqual(result.price_format_issues[0].row_number, 7)
        self.assertEqual(result.price_format_issues[0].value, "abc")

        self.assertEqual([item.material_key for item in result.would_be_added], ["sample_sand"])
        self.assertEqual([item.material_key for item in result.would_be_updated], ["sample_concrete"])
        self.assertEqual(
            result.would_be_updated[0].changed_fields,
            ["unit_price"],
        )
        self.assertEqual([item.material_key for item in result.would_be_unchanged], ["sample_unchanged"])

    def test_preview_report_is_markdown_and_safety_first(self):
        result = dry_run_owner_pricing_import(self.csv_path, self.current_path)
        report_path = os.path.join(self.test_dir.name, "preview.md")

        write_preview_report(result, report_path)

        with open(report_path, "r", encoding="utf-8") as file:
            report = file.read()

        self.assertIn("# Owner Pricing Import Dry-run Preview", report)
        self.assertIn("| CSV rows read | 7 |", report)
        self.assertIn("| Materials that would be updated | 1 |", report)
        self.assertIn("`sample_rebar`", report)
        self.assertIn("No live JSON or production pricing data was mutated.", report)

    def test_cli_writes_preview_report(self):
        report_path = os.path.join(self.test_dir.name, "cli_preview.md")
        env = os.environ.copy()
        src_path = os.path.abspath(os.path.join(os.getcwd(), "src"))
        env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "asset_factory.main",
                "owner-pricing-dry-run",
                "--csv",
                self.csv_path,
                "--current-pricing",
                self.current_path,
                "--report",
                report_path,
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(os.path.exists(report_path))
        self.assertIn("CSV rows read: 7", result.stdout)
        self.assertIn("Would be updated: 1", result.stdout)


if __name__ == "__main__":
    unittest.main()
