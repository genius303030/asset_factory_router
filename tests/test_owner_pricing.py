import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

from asset_factory.owner_pricing import (
    OWNER_PRICING_APPROVAL_PHRASE,
    dry_run_owner_pricing_import,
    run_owner_pricing_final_import_fake_rehearsal,
    write_owner_pricing_final_import_preflight,
    write_owner_pricing_approval_record,
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

    def test_approval_gate_writes_record_for_fake_sandbox_output(self):
        sandbox_output_path = os.path.join(
            os.getcwd(),
            "examples",
            "owner_pricing",
            "fake_sandbox_pricing_output.json",
        )
        plan_path = os.path.join(
            os.getcwd(),
            "examples",
            "owner_pricing",
            "fake_sandbox_apply_plan.md",
        )
        dry_run_report_path = os.path.join(
            os.getcwd(),
            "examples",
            "owner_pricing",
            "fake_preview_report.md",
        )
        approval_record_path = os.path.join(self.test_dir.name, "approval_record.json")
        markdown_summary_path = os.path.join(self.test_dir.name, "approval_record.md")

        result = write_owner_pricing_approval_record(
            sandbox_output_path=sandbox_output_path,
            sandbox_apply_plan_path=plan_path,
            dry_run_report_path=dry_run_report_path,
            owner_approval=OWNER_PRICING_APPROVAL_PHRASE,
            approval_record_path=approval_record_path,
            markdown_summary_path=markdown_summary_path,
        )

        self.assertTrue(os.path.exists(approval_record_path))
        self.assertTrue(os.path.exists(markdown_summary_path))
        self.assertEqual(result.approved_by, "local owner / manual owner")

        with open(sandbox_output_path, "rb") as file:
            expected_sha256 = hashlib.sha256(file.read()).hexdigest()
        self.assertEqual(result.sandbox_output_sha256, expected_sha256)

        with open(approval_record_path, "r", encoding="utf-8") as file:
            approval_record = json.load(file)

        self.assertEqual(
            approval_record["approval_type"],
            "owner_pricing_sandbox_output_approval",
        )
        self.assertTrue(approval_record["sandbox_only"])
        self.assertEqual(
            approval_record["approval_phrase_used"],
            OWNER_PRICING_APPROVAL_PHRASE,
        )
        self.assertEqual(
            approval_record["sandbox_output"]["sha256"],
            expected_sha256,
        )
        self.assertEqual(
            approval_record["sandbox_apply_plan"]["path"],
            plan_path,
        )
        self.assertEqual(
            approval_record["dry_run_report"]["path"],
            dry_run_report_path,
        )
        self.assertFalse(approval_record["final_import_enabled"])
        self.assertFalse(approval_record["live_json_mutated"])
        self.assertFalse(approval_record["production_pricing_mutated"])
        self.assertGreaterEqual(len(approval_record["checklist"]), 5)

        with open(markdown_summary_path, "r", encoding="utf-8") as file:
            markdown = file.read()
        self.assertIn("# Owner Pricing Approval Record Summary", markdown)
        self.assertIn("Final import remains disabled", json.dumps(approval_record))

    def test_approval_gate_requires_approval_phrase(self):
        sandbox_output_path = os.path.join(
            os.getcwd(),
            "examples",
            "owner_pricing",
            "fake_sandbox_pricing_output.json",
        )
        approval_record_path = os.path.join(self.test_dir.name, "approval_record.json")

        with self.assertRaisesRegex(ValueError, "approval phrase is required"):
            write_owner_pricing_approval_record(
                sandbox_output_path=sandbox_output_path,
                owner_approval="",
                approval_record_path=approval_record_path,
            )

    def test_approval_gate_requires_sandbox_output_path(self):
        approval_record_path = os.path.join(self.test_dir.name, "approval_record.json")

        with self.assertRaisesRegex(ValueError, "sandbox output path is required"):
            write_owner_pricing_approval_record(
                sandbox_output_path="",
                owner_approval=OWNER_PRICING_APPROVAL_PHRASE,
                approval_record_path=approval_record_path,
            )

    def test_approval_gate_requires_approval_output_path(self):
        sandbox_output_path = os.path.join(
            os.getcwd(),
            "examples",
            "owner_pricing",
            "fake_sandbox_pricing_output.json",
        )

        with self.assertRaisesRegex(ValueError, "approval record path is required"):
            write_owner_pricing_approval_record(
                sandbox_output_path=sandbox_output_path,
                owner_approval=OWNER_PRICING_APPROVAL_PHRASE,
                approval_record_path="",
            )

    def test_approval_gate_rejects_wrong_approval_phrase(self):
        sandbox_output_path = os.path.join(
            os.getcwd(),
            "examples",
            "owner_pricing",
            "fake_sandbox_pricing_output.json",
        )
        approval_record_path = os.path.join(self.test_dir.name, "approval_record.json")

        with self.assertRaisesRegex(ValueError, "approval phrase is incorrect"):
            write_owner_pricing_approval_record(
                sandbox_output_path=sandbox_output_path,
                owner_approval="I_APPROVE_PRODUCTION_IMPORT",
                approval_record_path=approval_record_path,
            )

    def test_approval_gate_requires_existing_sandbox_output(self):
        missing_sandbox_output = os.path.join(self.test_dir.name, "missing_sandbox.json")
        approval_record_path = os.path.join(self.test_dir.name, "approval_record.json")

        with self.assertRaisesRegex(FileNotFoundError, "does not exist"):
            write_owner_pricing_approval_record(
                sandbox_output_path=missing_sandbox_output,
                owner_approval=OWNER_PRICING_APPROVAL_PHRASE,
                approval_record_path=approval_record_path,
            )

    def test_approval_gate_rejects_non_json_sandbox_output(self):
        sandbox_output_path = os.path.join(self.test_dir.name, "sandbox_output.txt")
        approval_record_path = os.path.join(self.test_dir.name, "approval_record.json")
        with open(sandbox_output_path, "w", encoding="utf-8") as file:
            file.write("not json")

        with self.assertRaisesRegex(ValueError, "must be JSON"):
            write_owner_pricing_approval_record(
                sandbox_output_path=sandbox_output_path,
                owner_approval=OWNER_PRICING_APPROVAL_PHRASE,
                approval_record_path=approval_record_path,
            )

    def test_approval_gate_rejects_sandbox_only_false(self):
        sandbox_output_path = os.path.join(self.test_dir.name, "sandbox_output.json")
        approval_record_path = os.path.join(self.test_dir.name, "approval_record.json")
        with open(sandbox_output_path, "w", encoding="utf-8") as file:
            json.dump({"sandbox_only": False, "final_import_enabled": False}, file)

        with self.assertRaisesRegex(ValueError, "sandbox_only true"):
            write_owner_pricing_approval_record(
                sandbox_output_path=sandbox_output_path,
                owner_approval=OWNER_PRICING_APPROVAL_PHRASE,
                approval_record_path=approval_record_path,
            )

    def test_approval_gate_rejects_final_import_enabled_sandbox_output(self):
        sandbox_output_path = os.path.join(self.test_dir.name, "sandbox_output.json")
        approval_record_path = os.path.join(self.test_dir.name, "approval_record.json")
        with open(sandbox_output_path, "w", encoding="utf-8") as file:
            json.dump({"sandbox_only": True, "final_import_enabled": True}, file)

        with self.assertRaisesRegex(ValueError, "final import"):
            write_owner_pricing_approval_record(
                sandbox_output_path=sandbox_output_path,
                owner_approval=OWNER_PRICING_APPROVAL_PHRASE,
                approval_record_path=approval_record_path,
            )

    def test_approval_gate_blocks_live_prod_config_data_src_output_paths(self):
        sandbox_output_path = os.path.join(
            os.getcwd(),
            "examples",
            "owner_pricing",
            "fake_sandbox_pricing_output.json",
        )

        for path_part in ["live", "prod", "production", "config", "data", "src"]:
            with self.subTest(path_part=path_part):
                approval_record_path = os.path.join(
                    self.test_dir.name,
                    path_part,
                    "approval_record.json",
                )
                with self.assertRaisesRegex(ValueError, "live or production"):
                    write_owner_pricing_approval_record(
                        sandbox_output_path=sandbox_output_path,
                        owner_approval=OWNER_PRICING_APPROVAL_PHRASE,
                        approval_record_path=approval_record_path,
                    )

    def test_approval_gate_refuses_overwrite_without_flag(self):
        sandbox_output_path = os.path.join(
            os.getcwd(),
            "examples",
            "owner_pricing",
            "fake_sandbox_pricing_output.json",
        )
        approval_record_path = os.path.join(self.test_dir.name, "approval_record.json")

        write_owner_pricing_approval_record(
            sandbox_output_path=sandbox_output_path,
            owner_approval=OWNER_PRICING_APPROVAL_PHRASE,
            approval_record_path=approval_record_path,
        )

        with self.assertRaisesRegex(FileExistsError, "--overwrite"):
            write_owner_pricing_approval_record(
                sandbox_output_path=sandbox_output_path,
                owner_approval=OWNER_PRICING_APPROVAL_PHRASE,
                approval_record_path=approval_record_path,
            )

    def test_approval_gate_overwrite_flag_is_explicit(self):
        sandbox_output_path = os.path.join(
            os.getcwd(),
            "examples",
            "owner_pricing",
            "fake_sandbox_pricing_output.json",
        )
        approval_record_path = os.path.join(self.test_dir.name, "approval_record.json")

        write_owner_pricing_approval_record(
            sandbox_output_path=sandbox_output_path,
            owner_approval=OWNER_PRICING_APPROVAL_PHRASE,
            approval_record_path=approval_record_path,
        )
        write_owner_pricing_approval_record(
            sandbox_output_path=sandbox_output_path,
            owner_approval=OWNER_PRICING_APPROVAL_PHRASE,
            approval_record_path=approval_record_path,
            overwrite=True,
        )

        self.assertTrue(os.path.exists(approval_record_path))

    def test_approval_gate_does_not_mutate_sandbox_output(self):
        sandbox_output_path = os.path.join(
            os.getcwd(),
            "examples",
            "owner_pricing",
            "fake_sandbox_pricing_output.json",
        )
        approval_record_path = os.path.join(self.test_dir.name, "approval_record.json")

        with open(sandbox_output_path, "rb") as file:
            before = file.read()

        write_owner_pricing_approval_record(
            sandbox_output_path=sandbox_output_path,
            owner_approval=OWNER_PRICING_APPROVAL_PHRASE,
            approval_record_path=approval_record_path,
        )

        with open(sandbox_output_path, "rb") as file:
            after = file.read()

        self.assertEqual(after, before)

    def test_cli_approval_gate_writes_record(self):
        sandbox_output_path = os.path.join(
            os.getcwd(),
            "examples",
            "owner_pricing",
            "fake_sandbox_pricing_output.json",
        )
        approval_record_path = os.path.join(self.test_dir.name, "cli_approval_record.json")
        markdown_summary_path = os.path.join(self.test_dir.name, "cli_approval_record.md")
        env = os.environ.copy()
        src_path = os.path.abspath(os.path.join(os.getcwd(), "src"))
        env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "asset_factory.main",
                "owner-pricing-approve-sandbox-output",
                "--sandbox-output",
                sandbox_output_path,
                "--owner-approval",
                OWNER_PRICING_APPROVAL_PHRASE,
                "--approval-record",
                approval_record_path,
                "--markdown-summary",
                markdown_summary_path,
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(os.path.exists(approval_record_path))
        self.assertTrue(os.path.exists(markdown_summary_path))
        self.assertIn("Owner Pricing Approval Gate", result.stdout)
        self.assertIn("Final import enabled: false", result.stdout)

    def test_cli_approval_gate_rejects_wrong_phrase(self):
        sandbox_output_path = os.path.join(
            os.getcwd(),
            "examples",
            "owner_pricing",
            "fake_sandbox_pricing_output.json",
        )
        approval_record_path = os.path.join(self.test_dir.name, "cli_approval_record.json")
        env = os.environ.copy()
        src_path = os.path.abspath(os.path.join(os.getcwd(), "src"))
        env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "asset_factory.main",
                "owner-pricing-approve-sandbox-output",
                "--sandbox-output",
                sandbox_output_path,
                "--owner-approval",
                "WRONG",
                "--approval-record",
                approval_record_path,
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("approval phrase is incorrect", result.stderr)
        self.assertFalse(os.path.exists(approval_record_path))

    def test_cli_does_not_add_final_import_command(self):
        env = os.environ.copy()
        src_path = os.path.abspath(os.path.join(os.getcwd(), "src"))
        env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "asset_factory.main",
                "--help",
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertNotRegex(
            result.stdout,
            r"owner-pricing-final-import(?!-(?:preflight|fake-rehearsal))",
        )
        self.assertNotIn("production-import", result.stdout)

    def test_fake_example_approval_record_is_committed_output_shape(self):
        example_path = os.path.join(
            os.getcwd(),
            "examples",
            "owner_pricing",
            "fake_owner_pricing_approval_record.json",
        )

        with open(example_path, "r", encoding="utf-8") as file:
            approval_record = json.load(file)

        self.assertEqual(
            approval_record["approval_type"],
            "owner_pricing_sandbox_output_approval",
        )
        self.assertEqual(
            approval_record["approval_phrase_used"],
            OWNER_PRICING_APPROVAL_PHRASE,
        )
        self.assertRegex(approval_record["sandbox_output"]["sha256"], r"^[0-9a-f]{64}$")
        self.assertFalse(approval_record["final_import_enabled"])
        self.assertFalse(approval_record["live_json_mutated"])
        self.assertFalse(approval_record["production_pricing_mutated"])

    def _fake_sandbox_output_path(self):
        return os.path.join(
            os.getcwd(),
            "examples",
            "owner_pricing",
            "fake_sandbox_pricing_output.json",
        )

    def _fake_approval_record_path(self):
        return os.path.join(
            os.getcwd(),
            "examples",
            "owner_pricing",
            "fake_owner_pricing_approval_record.json",
        )

    def _write_temp_production_target(self):
        production_target_path = os.path.join(self.test_dir.name, "production_target.csv")
        with open(production_target_path, "w", encoding="utf-8") as file:
            file.write(CURRENT_PRICING_SAMPLE)
        return production_target_path

    def _write_fake_production_target(self):
        fake_target_path = os.path.join(self.test_dir.name, "fake_production_target.csv")
        with open(fake_target_path, "w", encoding="utf-8") as file:
            file.write(CURRENT_PRICING_SAMPLE)
        return fake_target_path

    def _write_matching_temp_approval_record(self, sandbox_output_path):
        with open(self._fake_approval_record_path(), "r", encoding="utf-8") as file:
            approval_record = json.load(file)
        with open(sandbox_output_path, "rb") as file:
            sandbox_sha256 = hashlib.sha256(file.read()).hexdigest()

        approval_record["sandbox_output"]["path"] = sandbox_output_path
        approval_record["sandbox_output"]["sha256"] = sandbox_sha256
        approval_record_path = os.path.join(self.test_dir.name, "approval_record.json")
        with open(approval_record_path, "w", encoding="utf-8") as file:
            json.dump(approval_record, file, indent=2)
            file.write("\n")
        return approval_record_path

    def _write_matching_fake_preflight_report(
        self,
        sandbox_output_path,
        approval_record_path,
        fake_production_target_path,
        backup_output_path,
    ):
        with open(sandbox_output_path, "rb") as file:
            sandbox_sha256 = hashlib.sha256(file.read()).hexdigest()
        with open(approval_record_path, "rb") as file:
            approval_sha256 = hashlib.sha256(file.read()).hexdigest()
        with open(fake_production_target_path, "rb") as file:
            production_sha256 = hashlib.sha256(file.read()).hexdigest()

        preflight = {
            "preflight_type": "owner_pricing_final_import_preflight",
            "status": "PASS",
            "generated_at": "2026-06-29T00:00:00+00:00",
            "checked_paths": {
                "sandbox_output": sandbox_output_path,
                "approval_record": approval_record_path,
                "production_target": fake_production_target_path,
                "backup_output": backup_output_path,
                "report": "fake_preflight_report.md",
                "report_json": "fake_preflight_report.json",
            },
            "checksums": {
                "sandbox_output_sha256": sandbox_sha256,
                "approval_record_sha256": approval_sha256,
                "production_target_sha256": production_sha256,
            },
            "validation_results": [],
            "blockers": [],
            "warnings": [],
            "production_write_performed": False,
            "backup_written": False,
            "live_json_mutated": False,
            "production_pricing_mutated": False,
        }
        preflight_path = os.path.join(self.test_dir.name, "fake_preflight_report.json")
        with open(preflight_path, "w", encoding="utf-8") as file:
            json.dump(preflight, file, indent=2)
            file.write("\n")
        return preflight_path

    def _fake_rehearsal_paths(self):
        return {
            "fake_output": os.path.join(self.test_dir.name, "fake_production_output.csv"),
            "backup": os.path.join(self.test_dir.name, "fake_backup_output.csv"),
            "audit": os.path.join(self.test_dir.name, "fake_rehearsal_audit.json"),
            "report": os.path.join(self.test_dir.name, "fake_rehearsal_report.md"),
        }

    def _run_fake_rehearsal(self, **overrides):
        paths = self._fake_rehearsal_paths()
        paths.update(overrides.pop("paths", {}))
        fake_target_path = overrides.pop("fake_target_path", None)
        if fake_target_path is None:
            fake_target_path = self._write_fake_production_target()
        sandbox_output_path = overrides.pop("sandbox_output_path", self._fake_sandbox_output_path())
        approval_record_path = overrides.pop("approval_record_path", self._fake_approval_record_path())
        preflight_report_path = overrides.pop("preflight_report_path", None)
        if preflight_report_path is None:
            preflight_report_path = self._write_matching_fake_preflight_report(
                sandbox_output_path,
                approval_record_path,
                fake_target_path,
                paths["backup"],
            )
        result = run_owner_pricing_final_import_fake_rehearsal(
            sandbox_output_path=sandbox_output_path,
            approval_record_path=approval_record_path,
            preflight_report_path=preflight_report_path,
            fake_production_target_path=fake_target_path,
            fake_production_output_path=paths["fake_output"],
            backup_output_path=paths["backup"],
            audit_log_path=paths["audit"],
            report_path=paths["report"],
            **overrides,
        )
        return result, paths, fake_target_path

    def test_preflight_command_success_with_fake_files(self):
        production_target_path = self._write_temp_production_target()
        report_path = os.path.join(self.test_dir.name, "preflight_report.md")
        report_json_path = os.path.join(self.test_dir.name, "preflight_report.json")
        backup_output_path = os.path.join(self.test_dir.name, "future_backup.json")

        result = write_owner_pricing_final_import_preflight(
            sandbox_output_path=self._fake_sandbox_output_path(),
            approval_record_path=self._fake_approval_record_path(),
            production_target_path=production_target_path,
            backup_output_path=backup_output_path,
            report_path=report_path,
            report_json_path=report_json_path,
        )

        self.assertTrue(result.passed)
        self.assertEqual(result.blockers, [])
        self.assertTrue(os.path.exists(report_path))
        self.assertTrue(os.path.exists(report_json_path))
        self.assertFalse(os.path.exists(backup_output_path))

        with open(report_path, "r", encoding="utf-8") as file:
            report = file.read()
        self.assertIn("Result: `PASS`", report)
        self.assertIn("No production write was performed.", report)

        with open(report_json_path, "r", encoding="utf-8") as file:
            report_json = json.load(file)
        self.assertEqual(report_json["status"], "PASS")
        self.assertFalse(report_json["production_write_performed"])
        self.assertFalse(report_json["live_json_mutated"])
        self.assertFalse(report_json["production_pricing_mutated"])
        self.assertFalse(report_json["backup_written"])

    def test_preflight_missing_sandbox_output_fails(self):
        production_target_path = self._write_temp_production_target()

        with self.assertRaisesRegex(FileNotFoundError, "sandbox output file does not exist"):
            write_owner_pricing_final_import_preflight(
                sandbox_output_path=os.path.join(self.test_dir.name, "missing.json"),
                approval_record_path=self._fake_approval_record_path(),
                production_target_path=production_target_path,
                backup_output_path=os.path.join(self.test_dir.name, "future_backup.json"),
                report_path=os.path.join(self.test_dir.name, "preflight_report.md"),
            )

    def test_preflight_invalid_sandbox_json_fails(self):
        production_target_path = self._write_temp_production_target()
        sandbox_output_path = os.path.join(self.test_dir.name, "sandbox_output.json")
        with open(sandbox_output_path, "w", encoding="utf-8") as file:
            file.write("{not json")

        with self.assertRaisesRegex(ValueError, "sandbox output must be JSON"):
            write_owner_pricing_final_import_preflight(
                sandbox_output_path=sandbox_output_path,
                approval_record_path=self._fake_approval_record_path(),
                production_target_path=production_target_path,
                backup_output_path=os.path.join(self.test_dir.name, "future_backup.json"),
                report_path=os.path.join(self.test_dir.name, "preflight_report.md"),
            )

    def test_preflight_sandbox_only_false_fails(self):
        production_target_path = self._write_temp_production_target()
        sandbox_output_path = os.path.join(self.test_dir.name, "sandbox_output.json")
        with open(sandbox_output_path, "w", encoding="utf-8") as file:
            json.dump({"sandbox_only": False, "final_import_enabled": False}, file)

        with self.assertRaisesRegex(ValueError, "sandbox_only true"):
            write_owner_pricing_final_import_preflight(
                sandbox_output_path=sandbox_output_path,
                approval_record_path=self._fake_approval_record_path(),
                production_target_path=production_target_path,
                backup_output_path=os.path.join(self.test_dir.name, "future_backup.json"),
                report_path=os.path.join(self.test_dir.name, "preflight_report.md"),
            )

    def test_preflight_final_import_enabled_true_fails(self):
        production_target_path = self._write_temp_production_target()
        sandbox_output_path = os.path.join(self.test_dir.name, "sandbox_output.json")
        with open(sandbox_output_path, "w", encoding="utf-8") as file:
            json.dump({"sandbox_only": True, "final_import_enabled": True}, file)

        with self.assertRaisesRegex(ValueError, "final import"):
            write_owner_pricing_final_import_preflight(
                sandbox_output_path=sandbox_output_path,
                approval_record_path=self._fake_approval_record_path(),
                production_target_path=production_target_path,
                backup_output_path=os.path.join(self.test_dir.name, "future_backup.json"),
                report_path=os.path.join(self.test_dir.name, "preflight_report.md"),
            )

    def test_preflight_missing_approval_record_fails(self):
        production_target_path = self._write_temp_production_target()

        with self.assertRaisesRegex(FileNotFoundError, "approval record file does not exist"):
            write_owner_pricing_final_import_preflight(
                sandbox_output_path=self._fake_sandbox_output_path(),
                approval_record_path=os.path.join(self.test_dir.name, "missing_approval.json"),
                production_target_path=production_target_path,
                backup_output_path=os.path.join(self.test_dir.name, "future_backup.json"),
                report_path=os.path.join(self.test_dir.name, "preflight_report.md"),
            )

    def test_preflight_approval_checksum_mismatch_fails_with_report(self):
        production_target_path = self._write_temp_production_target()
        approval_record_path = os.path.join(self.test_dir.name, "approval_record.json")
        with open(self._fake_approval_record_path(), "r", encoding="utf-8") as file:
            approval_record = json.load(file)
        approval_record["sandbox_output"]["sha256"] = "0" * 64
        with open(approval_record_path, "w", encoding="utf-8") as file:
            json.dump(approval_record, file, indent=2)
            file.write("\n")

        report_path = os.path.join(self.test_dir.name, "preflight_report.md")
        with self.assertRaisesRegex(ValueError, "preflight failed"):
            write_owner_pricing_final_import_preflight(
                sandbox_output_path=self._fake_sandbox_output_path(),
                approval_record_path=approval_record_path,
                production_target_path=production_target_path,
                backup_output_path=os.path.join(self.test_dir.name, "future_backup.json"),
                report_path=report_path,
            )

        self.assertTrue(os.path.exists(report_path))
        with open(report_path, "r", encoding="utf-8") as file:
            report = file.read()
        self.assertIn("Result: `FAIL`", report)
        self.assertIn("approval checksum does not match", report)

    def test_preflight_unsafe_production_target_path_fails(self):
        with self.assertRaisesRegex(ValueError, "production target path appears unsafe"):
            write_owner_pricing_final_import_preflight(
                sandbox_output_path=self._fake_sandbox_output_path(),
                approval_record_path=self._fake_approval_record_path(),
                production_target_path=os.path.join(self.test_dir.name, "prod", "target.csv"),
                backup_output_path=os.path.join(self.test_dir.name, "future_backup.json"),
                report_path=os.path.join(self.test_dir.name, "preflight_report.md"),
            )

    def test_preflight_unsafe_backup_path_fails(self):
        production_target_path = self._write_temp_production_target()

        with self.assertRaisesRegex(ValueError, "backup output path appears to target live or production"):
            write_owner_pricing_final_import_preflight(
                sandbox_output_path=self._fake_sandbox_output_path(),
                approval_record_path=self._fake_approval_record_path(),
                production_target_path=production_target_path,
                backup_output_path=os.path.join(self.test_dir.name, "live", "future_backup.json"),
                report_path=os.path.join(self.test_dir.name, "preflight_report.md"),
            )

    def test_preflight_duplicate_sandbox_material_keys_fail(self):
        production_target_path = self._write_temp_production_target()
        sandbox_output_path = os.path.join(self.test_dir.name, "sandbox_output.json")
        with open(self._fake_sandbox_output_path(), "r", encoding="utf-8") as file:
            sandbox_output = json.load(file)
        sandbox_output["materials"].append(dict(sandbox_output["materials"][0]))
        with open(sandbox_output_path, "w", encoding="utf-8") as file:
            json.dump(sandbox_output, file, indent=2)
            file.write("\n")
        approval_record_path = self._write_matching_temp_approval_record(sandbox_output_path)

        report_path = os.path.join(self.test_dir.name, "preflight_report.md")
        with self.assertRaisesRegex(ValueError, "preflight failed"):
            write_owner_pricing_final_import_preflight(
                sandbox_output_path=sandbox_output_path,
                approval_record_path=approval_record_path,
                production_target_path=production_target_path,
                backup_output_path=os.path.join(self.test_dir.name, "future_backup.json"),
                report_path=report_path,
            )

        with open(report_path, "r", encoding="utf-8") as file:
            report = file.read()
        self.assertIn("duplicate sandbox material keys", report)

    def test_preflight_count_mismatch_fails(self):
        production_target_path = self._write_temp_production_target()
        sandbox_output_path = os.path.join(self.test_dir.name, "sandbox_output.json")
        with open(self._fake_sandbox_output_path(), "r", encoding="utf-8") as file:
            sandbox_output = json.load(file)
        sandbox_output["summary"]["added_materials"] = 99
        with open(sandbox_output_path, "w", encoding="utf-8") as file:
            json.dump(sandbox_output, file, indent=2)
            file.write("\n")
        approval_record_path = self._write_matching_temp_approval_record(sandbox_output_path)

        with self.assertRaisesRegex(ValueError, "preflight failed"):
            write_owner_pricing_final_import_preflight(
                sandbox_output_path=sandbox_output_path,
                approval_record_path=approval_record_path,
                production_target_path=production_target_path,
                backup_output_path=os.path.join(self.test_dir.name, "future_backup.json"),
                report_path=os.path.join(self.test_dir.name, "preflight_report.md"),
            )

    def test_preflight_report_output_required(self):
        production_target_path = self._write_temp_production_target()

        with self.assertRaisesRegex(ValueError, "preflight report path is required"):
            write_owner_pricing_final_import_preflight(
                sandbox_output_path=self._fake_sandbox_output_path(),
                approval_record_path=self._fake_approval_record_path(),
                production_target_path=production_target_path,
                backup_output_path=os.path.join(self.test_dir.name, "future_backup.json"),
                report_path="",
            )

    def test_preflight_report_refuses_overwrite_without_flag(self):
        production_target_path = self._write_temp_production_target()
        report_path = os.path.join(self.test_dir.name, "preflight_report.md")

        write_owner_pricing_final_import_preflight(
            sandbox_output_path=self._fake_sandbox_output_path(),
            approval_record_path=self._fake_approval_record_path(),
            production_target_path=production_target_path,
            backup_output_path=os.path.join(self.test_dir.name, "future_backup.json"),
            report_path=report_path,
        )

        with self.assertRaisesRegex(FileExistsError, "--overwrite"):
            write_owner_pricing_final_import_preflight(
                sandbox_output_path=self._fake_sandbox_output_path(),
                approval_record_path=self._fake_approval_record_path(),
                production_target_path=production_target_path,
                backup_output_path=os.path.join(self.test_dir.name, "future_backup_2.json"),
                report_path=report_path,
            )

    def test_preflight_report_cannot_match_production_target_even_with_overwrite(self):
        production_target_path = self._write_temp_production_target()
        with open(production_target_path, "rb") as file:
            production_before = file.read()

        with self.assertRaisesRegex(
            ValueError,
            "owner pricing preflight report path must be different from production target",
        ):
            write_owner_pricing_final_import_preflight(
                sandbox_output_path=self._fake_sandbox_output_path(),
                approval_record_path=self._fake_approval_record_path(),
                production_target_path=production_target_path,
                backup_output_path=os.path.join(self.test_dir.name, "future_backup.json"),
                report_path=production_target_path,
                overwrite=True,
            )

        with open(production_target_path, "rb") as file:
            production_after = file.read()
        self.assertEqual(production_after, production_before)

    def test_preflight_does_not_mutate_production_or_live_inputs(self):
        production_target_path = self._write_temp_production_target()
        with open(production_target_path, "rb") as file:
            production_before = file.read()
        with open(self._fake_sandbox_output_path(), "rb") as file:
            sandbox_before = file.read()

        backup_output_path = os.path.join(self.test_dir.name, "future_backup.json")
        write_owner_pricing_final_import_preflight(
            sandbox_output_path=self._fake_sandbox_output_path(),
            approval_record_path=self._fake_approval_record_path(),
            production_target_path=production_target_path,
            backup_output_path=backup_output_path,
            report_path=os.path.join(self.test_dir.name, "preflight_report.md"),
        )

        with open(production_target_path, "rb") as file:
            production_after = file.read()
        with open(self._fake_sandbox_output_path(), "rb") as file:
            sandbox_after = file.read()

        self.assertEqual(production_after, production_before)
        self.assertEqual(sandbox_after, sandbox_before)
        self.assertFalse(os.path.exists(backup_output_path))

    def test_cli_preflight_success_writes_report(self):
        production_target_path = self._write_temp_production_target()
        report_path = os.path.join(self.test_dir.name, "cli_preflight_report.md")
        report_json_path = os.path.join(self.test_dir.name, "cli_preflight_report.json")
        env = os.environ.copy()
        src_path = os.path.abspath(os.path.join(os.getcwd(), "src"))
        env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "asset_factory.main",
                "owner-pricing-final-import-preflight",
                "--sandbox-output",
                self._fake_sandbox_output_path(),
                "--approval-record",
                self._fake_approval_record_path(),
                "--production-target",
                production_target_path,
                "--backup-output",
                os.path.join(self.test_dir.name, "future_backup.json"),
                "--report",
                report_path,
                "--report-json",
                report_json_path,
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(os.path.exists(report_path))
        self.assertTrue(os.path.exists(report_json_path))
        self.assertIn("Status: PASS", result.stdout)
        self.assertIn("No production write performed.", result.stdout)

    def test_cli_preflight_checksum_mismatch_fails(self):
        production_target_path = self._write_temp_production_target()
        approval_record_path = os.path.join(self.test_dir.name, "approval_record.json")
        with open(self._fake_approval_record_path(), "r", encoding="utf-8") as file:
            approval_record = json.load(file)
        approval_record["sandbox_output"]["sha256"] = "1" * 64
        with open(approval_record_path, "w", encoding="utf-8") as file:
            json.dump(approval_record, file, indent=2)
            file.write("\n")
        env = os.environ.copy()
        src_path = os.path.abspath(os.path.join(os.getcwd(), "src"))
        env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "asset_factory.main",
                "owner-pricing-final-import-preflight",
                "--sandbox-output",
                self._fake_sandbox_output_path(),
                "--approval-record",
                approval_record_path,
                "--production-target",
                production_target_path,
                "--backup-output",
                os.path.join(self.test_dir.name, "future_backup.json"),
                "--report",
                os.path.join(self.test_dir.name, "cli_preflight_report.md"),
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("preflight failed", result.stderr)

    def test_cli_preflight_unsafe_paths_fail(self):
        production_target_path = self._write_temp_production_target()
        env = os.environ.copy()
        src_path = os.path.abspath(os.path.join(os.getcwd(), "src"))
        env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")

        unsafe_target = subprocess.run(
            [
                sys.executable,
                "-m",
                "asset_factory.main",
                "owner-pricing-final-import-preflight",
                "--sandbox-output",
                self._fake_sandbox_output_path(),
                "--approval-record",
                self._fake_approval_record_path(),
                "--production-target",
                os.path.join(self.test_dir.name, "production", "target.csv"),
                "--backup-output",
                os.path.join(self.test_dir.name, "future_backup.json"),
                "--report",
                os.path.join(self.test_dir.name, "cli_preflight_report.md"),
            ],
            capture_output=True,
            text=True,
            env=env,
        )
        unsafe_backup = subprocess.run(
            [
                sys.executable,
                "-m",
                "asset_factory.main",
                "owner-pricing-final-import-preflight",
                "--sandbox-output",
                self._fake_sandbox_output_path(),
                "--approval-record",
                self._fake_approval_record_path(),
                "--production-target",
                production_target_path,
                "--backup-output",
                os.path.join(self.test_dir.name, "prod", "future_backup.json"),
                "--report",
                os.path.join(self.test_dir.name, "cli_preflight_report_2.md"),
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        self.assertNotEqual(unsafe_target.returncode, 0)
        self.assertIn("production target path appears unsafe", unsafe_target.stderr)
        self.assertNotEqual(unsafe_backup.returncode, 0)
        self.assertIn("backup output path appears to target live or production", unsafe_backup.stderr)

    def test_fake_rehearsal_success_path_writes_fake_backup_and_rolls_back(self):
        result, paths, fake_target_path = self._run_fake_rehearsal()

        self.assertEqual(result.status, "rollback_passed")
        self.assertTrue(os.path.exists(paths["backup"]))
        self.assertTrue(os.path.exists(paths["fake_output"]))
        self.assertTrue(os.path.exists(paths["audit"]))
        self.assertTrue(os.path.exists(paths["report"]))

        with open(paths["audit"], "r", encoding="utf-8") as file:
            audit = json.load(file)
        states = [item["status"] for item in audit["state_history"]]
        self.assertIn("started", states)
        self.assertIn("backup_verified", states)
        self.assertIn("fake_write_completed", states)
        self.assertIn("passed", states)
        self.assertIn("rollback_passed", states)
        self.assertTrue(audit["fake_fixture_only"])
        self.assertFalse(audit["safety_flags"]["production_write_performed"])
        self.assertTrue(audit["safety_flags"]["fake_production_write_performed"])
        self.assertTrue(audit["safety_flags"]["backup_written"])
        self.assertFalse(audit["safety_flags"]["live_json_mutated"])
        self.assertFalse(audit["safety_flags"]["production_pricing_mutated"])
        self.assertEqual(
            audit["checksums"]["backup_sha256"],
            audit["checksums"]["pre_import_fake_production_sha256"],
        )

        with open(fake_target_path, "rb") as file:
            fake_target_bytes = file.read()
        with open(paths["fake_output"], "rb") as file:
            restored_bytes = file.read()
        self.assertEqual(restored_bytes, fake_target_bytes)

    def test_fake_rehearsal_checksum_mismatch_fails_closed_with_audit(self):
        fake_target_path = self._write_fake_production_target()
        paths = self._fake_rehearsal_paths()
        approval_record_path = os.path.join(self.test_dir.name, "fake_approval_record.json")
        with open(self._fake_approval_record_path(), "r", encoding="utf-8") as file:
            approval_record = json.load(file)
        approval_record["sandbox_output"]["sha256"] = "0" * 64
        with open(approval_record_path, "w", encoding="utf-8") as file:
            json.dump(approval_record, file, indent=2)
            file.write("\n")
        preflight_report_path = self._write_matching_fake_preflight_report(
            self._fake_sandbox_output_path(),
            approval_record_path,
            fake_target_path,
            paths["backup"],
        )

        with self.assertRaisesRegex(ValueError, "fake rehearsal failed"):
            run_owner_pricing_final_import_fake_rehearsal(
                sandbox_output_path=self._fake_sandbox_output_path(),
                approval_record_path=approval_record_path,
                preflight_report_path=preflight_report_path,
                fake_production_target_path=fake_target_path,
                fake_production_output_path=paths["fake_output"],
                backup_output_path=paths["backup"],
                audit_log_path=paths["audit"],
                report_path=paths["report"],
            )

        self.assertFalse(os.path.exists(paths["backup"]))
        self.assertFalse(os.path.exists(paths["fake_output"]))
        with open(paths["audit"], "r", encoding="utf-8") as file:
            audit = json.load(file)
        self.assertEqual(audit["status"], "aborted")
        self.assertIn("approval checksum does not match", "\n".join(audit["blockers"]))

    def test_fake_rehearsal_stale_preflight_fails_closed(self):
        fake_target_path = self._write_fake_production_target()
        paths = self._fake_rehearsal_paths()
        preflight_report_path = self._write_matching_fake_preflight_report(
            self._fake_sandbox_output_path(),
            self._fake_approval_record_path(),
            fake_target_path,
            paths["backup"],
        )
        with open(preflight_report_path, "r", encoding="utf-8") as file:
            preflight = json.load(file)
        preflight["status"] = "FAIL"
        with open(preflight_report_path, "w", encoding="utf-8") as file:
            json.dump(preflight, file, indent=2)
            file.write("\n")

        with self.assertRaisesRegex(ValueError, "fake rehearsal failed"):
            run_owner_pricing_final_import_fake_rehearsal(
                sandbox_output_path=self._fake_sandbox_output_path(),
                approval_record_path=self._fake_approval_record_path(),
                preflight_report_path=preflight_report_path,
                fake_production_target_path=fake_target_path,
                fake_production_output_path=paths["fake_output"],
                backup_output_path=paths["backup"],
                audit_log_path=paths["audit"],
                report_path=paths["report"],
            )

        with open(paths["audit"], "r", encoding="utf-8") as file:
            audit = json.load(file)
        self.assertEqual(audit["status"], "aborted")
        self.assertFalse(os.path.exists(paths["fake_output"]))

    def test_fake_rehearsal_unsafe_path_fails_closed(self):
        fake_target_path = self._write_fake_production_target()
        paths = self._fake_rehearsal_paths()
        preflight_report_path = self._write_matching_fake_preflight_report(
            self._fake_sandbox_output_path(),
            self._fake_approval_record_path(),
            fake_target_path,
            paths["backup"],
        )

        with self.assertRaisesRegex(ValueError, "fake production output path appears unsafe"):
            run_owner_pricing_final_import_fake_rehearsal(
                sandbox_output_path=self._fake_sandbox_output_path(),
                approval_record_path=self._fake_approval_record_path(),
                preflight_report_path=preflight_report_path,
                fake_production_target_path=fake_target_path,
                fake_production_output_path=os.path.join(self.test_dir.name, "prod", "fake_output.csv"),
                backup_output_path=paths["backup"],
                audit_log_path=paths["audit"],
                report_path=paths["report"],
            )

    def test_fake_rehearsal_backup_path_exists_fails_closed(self):
        fake_target_path = self._write_fake_production_target()
        paths = self._fake_rehearsal_paths()
        preflight_report_path = self._write_matching_fake_preflight_report(
            self._fake_sandbox_output_path(),
            self._fake_approval_record_path(),
            fake_target_path,
            paths["backup"],
        )
        with open(paths["backup"], "w", encoding="utf-8") as file:
            file.write("existing fake backup")

        with self.assertRaisesRegex(FileExistsError, "fake backup output"):
            run_owner_pricing_final_import_fake_rehearsal(
                sandbox_output_path=self._fake_sandbox_output_path(),
                approval_record_path=self._fake_approval_record_path(),
                preflight_report_path=preflight_report_path,
                fake_production_target_path=fake_target_path,
                fake_production_output_path=paths["fake_output"],
                backup_output_path=paths["backup"],
                audit_log_path=paths["audit"],
                report_path=paths["report"],
            )

        self.assertFalse(os.path.exists(paths["audit"]))
        self.assertFalse(os.path.exists(paths["fake_output"]))

    def test_fake_rehearsal_backup_write_failure_fails_closed(self):
        fake_target_path = self._write_fake_production_target()
        paths = self._fake_rehearsal_paths()
        fake_parent_file = os.path.join(self.test_dir.name, "fake_parent_file")
        with open(fake_parent_file, "w", encoding="utf-8") as file:
            file.write("not a directory")
        paths["backup"] = os.path.join(fake_parent_file, "fake_backup_output.csv")
        preflight_report_path = self._write_matching_fake_preflight_report(
            self._fake_sandbox_output_path(),
            self._fake_approval_record_path(),
            fake_target_path,
            paths["backup"],
        )

        with self.assertRaisesRegex(ValueError, "fake rehearsal failed"):
            run_owner_pricing_final_import_fake_rehearsal(
                sandbox_output_path=self._fake_sandbox_output_path(),
                approval_record_path=self._fake_approval_record_path(),
                preflight_report_path=preflight_report_path,
                fake_production_target_path=fake_target_path,
                fake_production_output_path=paths["fake_output"],
                backup_output_path=paths["backup"],
                audit_log_path=paths["audit"],
                report_path=paths["report"],
            )

        with open(paths["audit"], "r", encoding="utf-8") as file:
            audit = json.load(file)
        self.assertEqual(audit["status"], "failed_before_write")
        self.assertFalse(audit["safety_flags"]["fake_production_write_performed"])
        self.assertFalse(os.path.exists(paths["fake_output"]))

    def test_fake_rehearsal_post_write_failure_enters_rollback_required(self):
        result, paths, _fake_target_path = self._run_fake_rehearsal(
            simulate_post_write_validation_failure=True
        )

        self.assertEqual(result.status, "rollback_passed")
        with open(paths["audit"], "r", encoding="utf-8") as file:
            audit = json.load(file)
        states = [item["status"] for item in audit["state_history"]]
        self.assertIn("rollback_required", states)
        self.assertIn("rollback_passed", states)
        self.assertTrue(audit["rollback"]["required"])
        self.assertTrue(audit["post_write_blockers"])

    def test_fake_rehearsal_rollback_verification_failure_is_captured(self):
        paths = self._fake_rehearsal_paths()

        with self.assertRaisesRegex(ValueError, "rollback failed"):
            self._run_fake_rehearsal(
                paths=paths,
                simulate_rollback_verification_failure=True,
            )

        with open(paths["audit"], "r", encoding="utf-8") as file:
            audit = json.load(file)
        self.assertEqual(audit["status"], "rollback_failed")
        states = [item["status"] for item in audit["state_history"]]
        self.assertIn("rollback_failed", states)
        self.assertTrue(audit["blockers"])

    def test_cli_fake_rehearsal_success_writes_audit_and_report(self):
        fake_target_path = self._write_fake_production_target()
        paths = self._fake_rehearsal_paths()
        preflight_report_path = self._write_matching_fake_preflight_report(
            self._fake_sandbox_output_path(),
            self._fake_approval_record_path(),
            fake_target_path,
            paths["backup"],
        )
        env = os.environ.copy()
        src_path = os.path.abspath(os.path.join(os.getcwd(), "src"))
        env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "asset_factory.main",
                "owner-pricing-final-import-fake-rehearsal",
                "--sandbox-output",
                self._fake_sandbox_output_path(),
                "--approval-record",
                self._fake_approval_record_path(),
                "--preflight-report",
                preflight_report_path,
                "--fake-production-target",
                fake_target_path,
                "--fake-production-output",
                paths["fake_output"],
                "--backup-output",
                paths["backup"],
                "--audit-log",
                paths["audit"],
                "--report",
                paths["report"],
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Status: rollback_passed", result.stdout)
        self.assertIn("No real production write performed.", result.stdout)
        self.assertTrue(os.path.exists(paths["audit"]))
        self.assertTrue(os.path.exists(paths["report"]))

    def test_cli_still_does_not_add_final_import_command(self):
        env = os.environ.copy()
        src_path = os.path.abspath(os.path.join(os.getcwd(), "src"))
        env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "asset_factory.main",
                "--help",
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("owner-pricing-final-import-preflight", result.stdout)
        self.assertIn("owner-pricing-final-import-fake-rehearsal", result.stdout)
        self.assertNotIn("owner-pricing-final-import,", result.stdout)
        self.assertNotIn("owner-pricing-final-import ", result.stdout)
        self.assertNotIn("enable-production-import", result.stdout)

    def test_fake_example_fake_rehearsal_audit_shape(self):
        example_path = os.path.join(
            os.getcwd(),
            "examples",
            "owner_pricing",
            "fake_final_import_rehearsal_audit.json",
        )

        with open(example_path, "r", encoding="utf-8") as file:
            audit = json.load(file)

        self.assertEqual(audit["audit_type"], "owner_pricing_final_import_fake_rehearsal")
        self.assertTrue(audit["fake_fixture_only"])
        self.assertEqual(audit["status"], "rollback_passed")
        self.assertFalse(audit["safety_flags"]["production_write_performed"])
        self.assertFalse(audit["safety_flags"]["live_json_mutated"])
        self.assertFalse(audit["safety_flags"]["production_pricing_mutated"])

    def test_fake_example_preflight_report_is_committed_output_shape(self):
        example_path = os.path.join(
            os.getcwd(),
            "examples",
            "owner_pricing",
            "fake_final_import_preflight_report.json",
        )

        with open(example_path, "r", encoding="utf-8") as file:
            preflight = json.load(file)

        self.assertEqual(preflight["preflight_type"], "owner_pricing_final_import_preflight")
        self.assertEqual(preflight["status"], "PASS")
        self.assertFalse(preflight["production_write_performed"])
        self.assertFalse(preflight["live_json_mutated"])
        self.assertFalse(preflight["production_pricing_mutated"])


if __name__ == "__main__":
    unittest.main()
