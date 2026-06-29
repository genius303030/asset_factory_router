import json
import os
import subprocess
import sys
import tempfile
import unittest

from asset_factory.owner_pricing import (
    dry_run_owner_pricing_import,
    write_sandbox_apply_output,
    write_sandbox_apply_plan,
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

    def test_sandbox_apply_plan_reports_review_requirements(self):
        plan_path = os.path.join(self.test_dir.name, "sandbox_plan.md")

        result = write_sandbox_apply_plan(
            csv_path=self.csv_path,
            current_pricing_path=self.current_path,
            plan_path=plan_path,
        )

        self.assertEqual(result.rows_read, 7)
        self.assertTrue(os.path.exists(plan_path))
        with open(plan_path, "r", encoding="utf-8") as file:
            plan = file.read()

        self.assertIn("# Owner Pricing Sandbox Apply Plan", plan)
        self.assertIn("| Invalid rows | 4 |", plan)
        self.assertIn("| Duplicate keys | 1 |", plan)
        self.assertIn("| Add candidates | 1 |", plan)
        self.assertIn("| Update candidates | 1 |", plan)
        self.assertIn("| Skipped rows | 4 |", plan)
        self.assertIn("Invalid rows exist; future apply is not recommended", plan)
        self.assertIn("Duplicate material keys exist; owner/G2 review is required.", plan)
        self.assertIn("duplicate material_key requires manual review", plan)
        self.assertIn("This plan does not import owner pricing into live JSON.", plan)

    def test_sandbox_apply_plan_json_output_is_optional_and_machine_readable(self):
        plan_path = os.path.join(self.test_dir.name, "sandbox_plan.md")
        json_path = os.path.join(self.test_dir.name, "sandbox_plan.json")

        write_sandbox_apply_plan(
            csv_path=self.csv_path,
            current_pricing_path=self.current_path,
            plan_path=plan_path,
            plan_json_path=json_path,
        )

        with open(json_path, "r", encoding="utf-8") as file:
            plan = json.load(file)

        self.assertTrue(plan["dry_run_only"])
        self.assertEqual(plan["plan_type"], "owner_pricing_sandbox_apply_plan")
        self.assertEqual(plan["summary"]["invalid_rows"], 4)
        self.assertEqual(plan["summary"]["duplicate_keys"], 1)
        self.assertEqual(plan["summary"]["add_candidates"], 1)
        self.assertEqual(plan["summary"]["update_candidates"], 1)
        self.assertEqual(plan["summary"]["unchanged_rows"], 1)
        self.assertEqual(len(plan["skipped_rows"]), 4)

    def test_sandbox_apply_plan_refuses_live_or_production_output_path(self):
        prod_plan_path = os.path.join(self.test_dir.name, "prod", "pricing_plan.md")

        with self.assertRaisesRegex(ValueError, "live or production"):
            write_sandbox_apply_plan(
                csv_path=self.csv_path,
                current_pricing_path=self.current_path,
                plan_path=prod_plan_path,
            )

    def test_sandbox_apply_plan_refuses_overwrite_without_flag(self):
        plan_path = os.path.join(self.test_dir.name, "sandbox_plan.md")

        write_sandbox_apply_plan(
            csv_path=self.csv_path,
            current_pricing_path=self.current_path,
            plan_path=plan_path,
        )

        with self.assertRaisesRegex(FileExistsError, "--overwrite"):
            write_sandbox_apply_plan(
                csv_path=self.csv_path,
                current_pricing_path=self.current_path,
                plan_path=plan_path,
            )

    def test_sandbox_apply_plan_overwrite_flag_is_explicit(self):
        plan_path = os.path.join(self.test_dir.name, "sandbox_plan.md")

        write_sandbox_apply_plan(
            csv_path=self.csv_path,
            current_pricing_path=self.current_path,
            plan_path=plan_path,
        )
        write_sandbox_apply_plan(
            csv_path=self.csv_path,
            current_pricing_path=self.current_path,
            plan_path=plan_path,
            overwrite=True,
        )

        self.assertTrue(os.path.exists(plan_path))

    def test_sandbox_apply_plan_does_not_mutate_current_pricing_snapshot(self):
        with open(self.current_path, "r", encoding="utf-8") as file:
            before = file.read()

        plan_path = os.path.join(self.test_dir.name, "sandbox_plan.md")
        write_sandbox_apply_plan(
            csv_path=self.csv_path,
            current_pricing_path=self.current_path,
            plan_path=plan_path,
        )

        with open(self.current_path, "r", encoding="utf-8") as file:
            after = file.read()

        self.assertEqual(after, before)

    def test_cli_sandbox_apply_plan_writes_outputs(self):
        plan_path = os.path.join(self.test_dir.name, "cli_sandbox_plan.md")
        json_path = os.path.join(self.test_dir.name, "cli_sandbox_plan.json")
        env = os.environ.copy()
        src_path = os.path.abspath(os.path.join(os.getcwd(), "src"))
        env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "asset_factory.main",
                "owner-pricing-plan-sandbox-apply",
                "--csv",
                self.csv_path,
                "--current-pricing",
                self.current_path,
                "--plan",
                plan_path,
                "--plan-json",
                json_path,
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(os.path.exists(plan_path))
        self.assertTrue(os.path.exists(json_path))
        self.assertIn("CSV rows read: 7", result.stdout)
        self.assertIn("Duplicate keys: 1", result.stdout)

    def test_cli_sandbox_apply_plan_requires_output_path(self):
        env = os.environ.copy()
        src_path = os.path.abspath(os.path.join(os.getcwd(), "src"))
        env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "asset_factory.main",
                "owner-pricing-plan-sandbox-apply",
                "--csv",
                self.csv_path,
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--plan", result.stderr)

    def test_fake_example_sandbox_apply_plan_is_committed_output_shape(self):
        example_path = os.path.join(
            os.getcwd(),
            "examples",
            "owner_pricing",
            "fake_sandbox_apply_plan.md",
        )

        with open(example_path, "r", encoding="utf-8") as file:
            plan = file.read()

        self.assertIn("# Owner Pricing Sandbox Apply Plan", plan)
        self.assertIn("| Total rows read | 7 |", plan)
        self.assertIn("sample_concrete", plan)

    def test_sandbox_apply_output_writes_sandbox_pricing_snapshot_and_summaries(self):
        plan_path = os.path.join(self.test_dir.name, "sandbox_plan.md")
        output_path = os.path.join(self.test_dir.name, "sandbox_pricing_output.json")
        summary_report_path = os.path.join(self.test_dir.name, "sandbox_output_summary.md")
        summary_json_path = os.path.join(self.test_dir.name, "sandbox_output_summary.json")
        write_sandbox_apply_plan(
            csv_path=self.csv_path,
            current_pricing_path=self.current_path,
            plan_path=plan_path,
        )

        result = write_sandbox_apply_output(
            csv_path=self.csv_path,
            current_pricing_path=self.current_path,
            sandbox_apply_plan_path=plan_path,
            sandbox_output_path=output_path,
            summary_report_path=summary_report_path,
            summary_json_path=summary_json_path,
        )

        self.assertEqual(result.rows_read, 7)
        self.assertEqual(result.valid_rows, 3)
        self.assertEqual(result.invalid_rows, 4)
        self.assertEqual(result.sandbox_materials_written, 4)
        self.assertTrue(os.path.exists(output_path))
        self.assertTrue(os.path.exists(summary_report_path))
        self.assertTrue(os.path.exists(summary_json_path))

        with open(output_path, "r", encoding="utf-8") as file:
            sandbox_output = json.load(file)

        self.assertEqual(
            sandbox_output["output_type"],
            "owner_pricing_sandbox_apply_output",
        )
        self.assertTrue(sandbox_output["sandbox_only"])
        self.assertFalse(sandbox_output["live_json_mutated"])
        self.assertFalse(sandbox_output["production_pricing_mutated"])
        self.assertFalse(sandbox_output["final_import_enabled"])
        self.assertEqual(sandbox_output["source_csv_path"], self.csv_path)
        self.assertEqual(sandbox_output["baseline_pricing_path"], self.current_path)
        self.assertEqual(sandbox_output["sandbox_apply_plan"]["path"], plan_path)
        self.assertEqual(sandbox_output["summary"]["added_materials"], 1)
        self.assertEqual(sandbox_output["summary"]["updated_materials"], 1)
        self.assertEqual(sandbox_output["summary"]["unchanged_materials"], 1)
        self.assertEqual(sandbox_output["summary"]["retained_baseline_materials"], 1)
        self.assertEqual(sandbox_output["summary"]["skipped_rows"], 4)

        materials_by_key = {
            material["material_key"]: material
            for material in sandbox_output["materials"]
        }
        self.assertEqual(
            sorted(materials_by_key),
            [
                "sample_concrete",
                "sample_old_only",
                "sample_sand",
                "sample_unchanged",
            ],
        )
        self.assertEqual(materials_by_key["sample_concrete"]["unit_price"], "125.50")
        self.assertEqual(materials_by_key["sample_concrete"]["sandbox_status"], "updated")
        self.assertEqual(materials_by_key["sample_sand"]["sandbox_status"], "added")
        self.assertEqual(
            materials_by_key["sample_old_only"]["sandbox_status"],
            "baseline_retained",
        )
        self.assertNotIn("sample_rebar", materials_by_key)
        self.assertNotIn("sample_missing_unit", materials_by_key)
        self.assertNotIn("sample_bad_price", materials_by_key)

        with open(summary_report_path, "r", encoding="utf-8") as file:
            report = file.read()
        self.assertIn("# Owner Pricing Sandbox Apply Output Summary", report)
        self.assertIn("| Sandbox materials written | 4 |", report)
        self.assertIn("final import remains disabled", report)

        with open(summary_json_path, "r", encoding="utf-8") as file:
            summary_json = json.load(file)
        self.assertEqual(
            summary_json["summary_type"],
            "owner_pricing_sandbox_apply_output_summary",
        )
        self.assertEqual(summary_json["summary"]["sandbox_materials_written"], 4)

    def test_sandbox_apply_output_requires_explicit_output_path(self):
        with self.assertRaisesRegex(ValueError, "path is required"):
            write_sandbox_apply_output(
                csv_path=self.csv_path,
                current_pricing_path=self.current_path,
                sandbox_output_path="",
            )

    def test_sandbox_apply_output_refuses_live_or_production_output_path(self):
        prod_output_path = os.path.join(self.test_dir.name, "production", "sandbox_output.json")

        with self.assertRaisesRegex(ValueError, "live or production"):
            write_sandbox_apply_output(
                csv_path=self.csv_path,
                current_pricing_path=self.current_path,
                sandbox_output_path=prod_output_path,
            )

    def test_sandbox_apply_output_refuses_common_pricing_filename(self):
        pricing_output_path = os.path.join(self.test_dir.name, "pricing.json")

        with self.assertRaisesRegex(ValueError, "live or production"):
            write_sandbox_apply_output(
                csv_path=self.csv_path,
                current_pricing_path=self.current_path,
                sandbox_output_path=pricing_output_path,
            )

    def test_sandbox_apply_output_refuses_overwrite_without_flag(self):
        output_path = os.path.join(self.test_dir.name, "sandbox_pricing_output.json")

        write_sandbox_apply_output(
            csv_path=self.csv_path,
            current_pricing_path=self.current_path,
            sandbox_output_path=output_path,
        )

        with self.assertRaisesRegex(FileExistsError, "--overwrite"):
            write_sandbox_apply_output(
                csv_path=self.csv_path,
                current_pricing_path=self.current_path,
                sandbox_output_path=output_path,
            )

    def test_sandbox_apply_output_overwrite_flag_is_explicit(self):
        output_path = os.path.join(self.test_dir.name, "sandbox_pricing_output.json")

        write_sandbox_apply_output(
            csv_path=self.csv_path,
            current_pricing_path=self.current_path,
            sandbox_output_path=output_path,
        )
        write_sandbox_apply_output(
            csv_path=self.csv_path,
            current_pricing_path=self.current_path,
            sandbox_output_path=output_path,
            overwrite=True,
        )

        self.assertTrue(os.path.exists(output_path))

    def test_sandbox_apply_output_does_not_mutate_live_json_baseline(self):
        live_json_path = os.path.join(self.test_dir.name, "live_pricing_baseline.json")
        live_json_data = {
            "materials": [
                {
                    "material_key": "sample_concrete",
                    "material_name": "Demo Concrete",
                    "unit": "bags",
                    "unit_price": "120.00",
                },
                {
                    "material_key": "sample_unchanged",
                    "material_name": "Demo Unchanged",
                    "unit": "kg",
                    "unit_price": "30.00",
                },
            ]
        }
        with open(live_json_path, "w", encoding="utf-8") as file:
            json.dump(live_json_data, file, indent=2)
            file.write("\n")
        with open(live_json_path, "r", encoding="utf-8") as file:
            before = file.read()

        output_path = os.path.join(self.test_dir.name, "sandbox_pricing_output.json")
        write_sandbox_apply_output(
            csv_path=self.csv_path,
            current_pricing_path=live_json_path,
            sandbox_output_path=output_path,
        )

        with open(live_json_path, "r", encoding="utf-8") as file:
            after = file.read()

        self.assertEqual(after, before)

    def test_sandbox_apply_output_does_not_mutate_production_pricing_snapshot(self):
        with open(self.current_path, "r", encoding="utf-8") as file:
            before = file.read()

        output_path = os.path.join(self.test_dir.name, "sandbox_pricing_output.json")
        write_sandbox_apply_output(
            csv_path=self.csv_path,
            current_pricing_path=self.current_path,
            sandbox_output_path=output_path,
        )

        with open(self.current_path, "r", encoding="utf-8") as file:
            after = file.read()

        self.assertEqual(after, before)

    def test_cli_sandbox_apply_output_writes_outputs(self):
        output_path = os.path.join(self.test_dir.name, "cli_sandbox_output.json")
        summary_report_path = os.path.join(self.test_dir.name, "cli_sandbox_summary.md")
        summary_json_path = os.path.join(self.test_dir.name, "cli_sandbox_summary.json")
        env = os.environ.copy()
        src_path = os.path.abspath(os.path.join(os.getcwd(), "src"))
        env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "asset_factory.main",
                "owner-pricing-apply-sandbox-output",
                "--csv",
                self.csv_path,
                "--current-pricing",
                self.current_path,
                "--output",
                output_path,
                "--summary-report",
                summary_report_path,
                "--summary-json",
                summary_json_path,
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(os.path.exists(output_path))
        self.assertTrue(os.path.exists(summary_report_path))
        self.assertTrue(os.path.exists(summary_json_path))
        self.assertIn("CSV rows read: 7", result.stdout)
        self.assertIn("Sandbox materials written: 4", result.stdout)
        self.assertIn("Duplicate keys: 1", result.stdout)

    def test_cli_sandbox_apply_output_requires_output_path(self):
        env = os.environ.copy()
        src_path = os.path.abspath(os.path.join(os.getcwd(), "src"))
        env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "asset_factory.main",
                "owner-pricing-apply-sandbox-output",
                "--csv",
                self.csv_path,
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--output", result.stderr)

    def test_fake_example_sandbox_apply_output_is_committed_output_shape(self):
        example_path = os.path.join(
            os.getcwd(),
            "examples",
            "owner_pricing",
            "fake_sandbox_pricing_output.json",
        )

        with open(example_path, "r", encoding="utf-8") as file:
            sandbox_output = json.load(file)

        self.assertEqual(
            sandbox_output["output_type"],
            "owner_pricing_sandbox_apply_output",
        )
        self.assertTrue(sandbox_output["sandbox_only"])
        self.assertFalse(sandbox_output["production_pricing_mutated"])
        self.assertEqual(sandbox_output["summary"]["sandbox_materials_written"], 4)
        self.assertEqual(sandbox_output["summary"]["skipped_rows"], 4)
        self.assertIn("sample_concrete", json.dumps(sandbox_output))


if __name__ == "__main__":
    unittest.main()
