import argparse
import os
import json
import logging
import dataclasses
from typing import Dict, Any

from .models import AssetPack
from .brief_loader import BriefLoader
from .prompt_engine import PromptEngine
from .router import ModelRouter
from .asset_pack_writer import AssetPackWriter

logger = logging.getLogger(__name__)

def setup_logging(debug: bool):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
        datefmt='%H:%main:%S'
    )

def create_pack(brief_path: str, out_dir: str):
    logger.info(f"Loading brief from {brief_path}")
    brief = BriefLoader.load_from_file(brief_path)
    logger.info(f"Loaded Brief: {brief.project_name}")
    
    # Generate router plan
    logger.info("Generating routing plan...")
    routing_plan = ModelRouter.generate_routing_plan(
        task_type=brief.task_type,
        style=brief.style,
        quality=brief.quality,
        speed=brief.speed,
        budget=brief.budget
    )
    logger.debug(f"Routing Plan generated: {routing_plan.recommended_provider}")
    
    # Generate prompts and contents
    logger.info("Initializing Prompt Engine...")
    engine = PromptEngine()
    
    # We need brief as a dict for prompt_engine V0.2
    brief_dict = dataclasses.asdict(brief)
    
    prompt_pack_md = engine.generate_prompt_pack(brief_dict, routing_plan)
    image_prompts = engine.generate_image_prompts_json(brief_dict)
    ui_style_guide_md = engine.generate_ui_style_guide(brief_dict)
    storyboard_md = engine.generate_storyboard(brief_dict)
    codex_task_md = engine.build_codex_task(brief)
    production_checklist_md = engine.build_production_checklist(brief)
    pack_summary_md = engine.build_pack_summary(brief, routing_plan)
    
    # Generate manifest
    asset_manifest = {
        "project": brief.project_name,
        "files_included": [
            "project_brief.json",
            "prompt_pack.md",
            "image_prompts.json",
            "ui_style_guide.md",
            "storyboard.md",
            "asset_manifest.json",
            "routing_plan.json",
            "codex_asset_tasks.md",
            "production_checklist.md",
            "pack_summary.md"
        ]
    }
    
    # Assemble pack
    pack = AssetPack(
        project_brief=brief,
        prompt_pack_md=prompt_pack_md,
        image_prompts=image_prompts,
        ui_style_guide_md=ui_style_guide_md,
        storyboard_md=storyboard_md,
        asset_manifest=asset_manifest,
        routing_plan=routing_plan,
        codex_task_md=codex_task_md,
        production_checklist_md=production_checklist_md,
        pack_summary_md=pack_summary_md
    )
    
    # Write output
    logger.info(f"Writing asset pack to {out_dir}...")
    AssetPackWriter.write(pack, out_dir)
    logger.info("Process complete.")

def demo():
    logger.info("Running DEMO mode...")
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    brief_path = os.path.join(base_dir, "examples", "tactical_panel_brief.json")
    out_dir = os.path.join(base_dir, "output", "demo_pack")
    create_pack(brief_path, out_dir)

def route(task: str, style: str, quality: str, budget: str, speed: str):
    logger.info(f"Evaluating route for task: {task}, style: {style}")
    plan = ModelRouter.generate_routing_plan(
        task_type=task,
        style=style,
        quality=quality,
        speed=speed,
        budget=budget
    )
    # Even in script mode, we probably want to print the route result to stdout
    print("\n--- Model Routing Plan ---")
    print(json.dumps(dataclasses.asdict(plan), indent=2, ensure_ascii=False))

def main():
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    parser = argparse.ArgumentParser(description="AI Asset Factory + Model Router V0.2", parents=[parent_parser])
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Demo command
    demo_parser = subparsers.add_parser("demo", parents=[parent_parser], help="Run a demo to generate a sample asset pack")

    # Create command
    create_parser = subparsers.add_parser("create", parents=[parent_parser], help="Create an asset pack from a brief")
    create_parser.add_argument("--brief", required=True, help="Path to the JSON brief file")
    create_parser.add_argument("--out", required=True, help="Output directory path")

    # Route command
    route_parser = subparsers.add_parser("route", parents=[parent_parser], help="Get a model routing plan")
    route_parser.add_argument("--task", required=True, help="Task type (e.g., image, video, ui)")
    route_parser.add_argument("--style", required=True, help="Style (e.g., realistic, tactical_ui)")
    route_parser.add_argument("--quality", default="medium", help="Quality (low, medium, high)")
    route_parser.add_argument("--speed", default="normal", help="Speed (slow, normal, fast)")
    route_parser.add_argument("--budget", default="medium", help="Budget (low, medium, high)")

    # Validate command
    validate_parser = subparsers.add_parser("validate", parents=[parent_parser], help="Validate a brief JSON")
    validate_parser.add_argument("--brief", required=True, help="Path to the JSON brief file")

    # Inspect command
    inspect_parser = subparsers.add_parser("inspect", parents=[parent_parser], help="Inspect an asset pack")
    inspect_parser.add_argument("--pack", required=True, help="Path to the asset pack directory")

    # List-providers command
    subparsers.add_parser("list-providers", parents=[parent_parser], help="List all registered providers")

    # Owner pricing dry-run command
    owner_pricing_parser = subparsers.add_parser(
        "owner-pricing-dry-run",
        parents=[parent_parser],
        help="Validate an owner pricing CSV and write a dry-run preview report",
    )
    owner_pricing_parser.add_argument("--csv", required=True, help="Path to the owner pricing CSV file")
    owner_pricing_parser.add_argument(
        "--current-pricing",
        help="Optional read-only current pricing snapshot, as CSV or JSON",
    )
    owner_pricing_parser.add_argument("--report", required=True, help="Path to write the markdown preview report")

    # Owner pricing sandbox apply plan command
    owner_pricing_plan_parser = subparsers.add_parser(
        "owner-pricing-plan-sandbox-apply",
        parents=[parent_parser],
        help="Create a reviewable sandbox apply plan from owner pricing CSV dry-run data",
    )
    owner_pricing_plan_parser.add_argument("--csv", required=True, help="Path to the owner pricing CSV file")
    owner_pricing_plan_parser.add_argument(
        "--current-pricing",
        help="Optional read-only current pricing snapshot, as CSV or JSON",
    )
    owner_pricing_plan_parser.add_argument(
        "--dry-run-report",
        help="Optional dry-run report to reference and read for traceability",
    )
    owner_pricing_plan_parser.add_argument("--plan", required=True, help="Path to write the markdown sandbox apply plan")
    owner_pricing_plan_parser.add_argument("--plan-json", help="Optional path to write a JSON sandbox apply plan")
    owner_pricing_plan_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting an existing sandbox plan output",
    )

    # Owner pricing sandbox apply output command
    owner_pricing_output_parser = subparsers.add_parser(
        "owner-pricing-apply-sandbox-output",
        aliases=["owner-pricing-sandbox-output"],
        parents=[parent_parser],
        help="Write sandbox-only owner pricing output from owner pricing CSV data",
    )
    owner_pricing_output_parser.add_argument("--csv", required=True, help="Path to the owner pricing CSV file")
    owner_pricing_output_parser.add_argument(
        "--current-pricing",
        help="Optional read-only current pricing snapshot, as CSV or JSON",
    )
    owner_pricing_output_parser.add_argument(
        "--sandbox-apply-plan",
        help="Optional sandbox apply plan from owner-pricing-plan-sandbox-apply",
    )
    owner_pricing_output_parser.add_argument(
        "--output",
        required=True,
        help="Explicit path to write the sandbox pricing output JSON",
    )
    owner_pricing_output_parser.add_argument(
        "--summary-report",
        help="Optional path to write a markdown sandbox output summary",
    )
    owner_pricing_output_parser.add_argument(
        "--summary-json",
        help="Optional path to write a JSON sandbox output summary",
    )
    owner_pricing_output_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting existing sandbox output files",
    )

    # Owner pricing approval gate command
    owner_pricing_approval_parser = subparsers.add_parser(
        "owner-pricing-approve-sandbox-output",
        aliases=["owner-pricing-approval-gate"],
        parents=[parent_parser],
        help="Write a manual owner approval record for a sandbox pricing output",
    )
    owner_pricing_approval_parser.add_argument(
        "--sandbox-output",
        required=True,
        help="Path to the sandbox pricing output JSON from owner-pricing-apply-sandbox-output",
    )
    owner_pricing_approval_parser.add_argument(
        "--sandbox-apply-plan",
        help="Optional sandbox apply plan to reference",
    )
    owner_pricing_approval_parser.add_argument(
        "--dry-run-report",
        help="Optional dry-run report to reference",
    )
    owner_pricing_approval_parser.add_argument(
        "--owner-approval",
        required=True,
        help="Required exact approval phrase: I_APPROVE_SANDBOX_PRICING_OUTPUT",
    )
    owner_pricing_approval_parser.add_argument(
        "--approved-by",
        default="local owner / manual owner",
        help="Manual approver label to include in the approval record",
    )
    owner_pricing_approval_parser.add_argument(
        "--approval-record",
        required=True,
        help="Explicit path to write the approval record JSON",
    )
    owner_pricing_approval_parser.add_argument(
        "--markdown-summary",
        help="Optional path to write a markdown approval summary",
    )
    owner_pricing_approval_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting an existing approval record output",
    )

    # Owner pricing final import preflight command
    owner_pricing_preflight_parser = subparsers.add_parser(
        "owner-pricing-final-import-preflight",
        aliases=["owner-pricing-preflight-final-import"],
        parents=[parent_parser],
        help="Run a read-only preflight check before any future owner pricing final import",
    )
    owner_pricing_preflight_parser.add_argument(
        "--sandbox-output",
        required=True,
        help="Path to the sandbox pricing output JSON",
    )
    owner_pricing_preflight_parser.add_argument(
        "--approval-record",
        required=True,
        help="Path to the owner approval record JSON",
    )
    owner_pricing_preflight_parser.add_argument(
        "--production-target",
        required=True,
        help="Explicit production pricing target path to inspect read-only",
    )
    owner_pricing_preflight_parser.add_argument(
        "--backup-output",
        required=True,
        help="Explicit future backup path to validate without writing",
    )
    owner_pricing_preflight_parser.add_argument(
        "--report",
        required=True,
        help="Path to write the markdown preflight report",
    )
    owner_pricing_preflight_parser.add_argument(
        "--report-json",
        help="Optional path to write a JSON preflight report",
    )
    owner_pricing_preflight_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting existing preflight report outputs",
    )

    # Owner pricing final import fake rehearsal command
    owner_pricing_fake_rehearsal_parser = subparsers.add_parser(
        "owner-pricing-final-import-fake-rehearsal",
        parents=[parent_parser],
        help="Run a fake-fixture-only rehearsal of final-import-adjacent mechanics",
    )
    owner_pricing_fake_rehearsal_parser.add_argument(
        "--sandbox-output",
        required=True,
        help="Path to the fake sandbox pricing output JSON",
    )
    owner_pricing_fake_rehearsal_parser.add_argument(
        "--approval-record",
        required=True,
        help="Path to the fake owner approval record JSON",
    )
    owner_pricing_fake_rehearsal_parser.add_argument(
        "--preflight-report",
        required=True,
        help="Path to the fake preflight report JSON",
    )
    owner_pricing_fake_rehearsal_parser.add_argument(
        "--fake-production-target",
        required=True,
        help="Explicit fake production target fixture to read",
    )
    owner_pricing_fake_rehearsal_parser.add_argument(
        "--fake-production-output",
        required=True,
        help="Explicit fake output path to write and restore",
    )
    owner_pricing_fake_rehearsal_parser.add_argument(
        "--backup-output",
        required=True,
        help="Explicit fake backup output path",
    )
    owner_pricing_fake_rehearsal_parser.add_argument(
        "--audit-log",
        required=True,
        help="Explicit fake rehearsal audit log path",
    )
    owner_pricing_fake_rehearsal_parser.add_argument(
        "--report",
        required=True,
        help="Explicit fake rehearsal markdown report path",
    )
    owner_pricing_fake_rehearsal_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting fake report, audit, and output paths; never backup",
    )
    owner_pricing_fake_rehearsal_parser.add_argument(
        "--simulate-post-write-validation-failure",
        action="store_true",
        help="Exercise rollback-required handling with fake duplicate output",
    )
    owner_pricing_fake_rehearsal_parser.add_argument(
        "--simulate-rollback-verification-failure",
        action="store_true",
        help="Exercise rollback-failed handling by corrupting fake restore output",
    )

    args = parser.parse_args()
    
    setup_logging(args.debug)

    try:
        if args.command == "demo":
            demo()
        elif args.command == "create":
            create_pack(args.brief, args.out)
        elif args.command == "route":
            route(args.task, args.style, args.quality, args.budget, args.speed)
        elif args.command == "validate":
            from .validator import BriefValidator
            result = BriefValidator.validate_file(args.brief)
            print("\n--- Validation Result ---")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif args.command == "inspect":
            from .inspector import PackInspector
            result = PackInspector.inspect(args.pack)
            print("\n--- Pack Inspection Result ---")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif args.command == "list-providers":
            from .providers.registry import ProviderRegistry
            registry = ProviderRegistry()
            print("\n--- Registered Providers ---")
            for p in registry.list_all():
                print(f"- {p.name}: Tasks={p.supported_tasks}, Quality={p.quality_level}, Speed={p.speed_level}, Cost={p.cost_level}")
        elif args.command == "owner-pricing-dry-run":
            from .owner_pricing import dry_run_owner_pricing_import, write_preview_report
            result = dry_run_owner_pricing_import(args.csv, args.current_pricing)
            write_preview_report(result, args.report)
            print("\n--- Owner Pricing Dry-run Preview ---")
            print(f"Report: {args.report}")
            print(f"CSV rows read: {result.rows_read}")
            print(f"Valid rows: {result.valid_rows}")
            print(f"Invalid rows: {result.invalid_rows}")
            print(f"Would be added: {len(result.would_be_added)}")
            print(f"Would be updated: {len(result.would_be_updated)}")
            print(f"Would be unchanged: {len(result.would_be_unchanged)}")
        elif args.command == "owner-pricing-plan-sandbox-apply":
            import sys
            from .owner_pricing import write_sandbox_apply_plan
            try:
                result = write_sandbox_apply_plan(
                    csv_path=args.csv,
                    current_pricing_path=args.current_pricing,
                    dry_run_report_path=args.dry_run_report,
                    plan_path=args.plan,
                    plan_json_path=args.plan_json,
                    overwrite=args.overwrite,
                )
            except Exception as e:
                print(f"Error: {str(e)}", file=sys.stderr)
                raise SystemExit(1)

            print("\n--- Owner Pricing Sandbox Apply Plan ---")
            print(f"Plan: {args.plan}")
            if args.plan_json:
                print(f"Plan JSON: {args.plan_json}")
            print(f"CSV rows read: {result.rows_read}")
            print(f"Valid rows: {result.valid_rows}")
            print(f"Invalid rows: {result.invalid_rows}")
            print(f"Add candidates: {len(result.would_be_added)}")
            print(f"Update candidates: {len(result.would_be_updated)}")
            print(f"Unchanged rows: {len(result.would_be_unchanged)}")
            print(f"Duplicate keys: {len(result.duplicate_material_keys)}")
        elif args.command in (
            "owner-pricing-apply-sandbox-output",
            "owner-pricing-sandbox-output",
        ):
            import sys
            from .owner_pricing import write_sandbox_apply_output
            try:
                result = write_sandbox_apply_output(
                    csv_path=args.csv,
                    current_pricing_path=args.current_pricing,
                    sandbox_apply_plan_path=args.sandbox_apply_plan,
                    sandbox_output_path=args.output,
                    summary_report_path=args.summary_report,
                    summary_json_path=args.summary_json,
                    overwrite=args.overwrite,
                )
            except Exception as e:
                print(f"Error: {str(e)}", file=sys.stderr)
                raise SystemExit(1)

            print("\n--- Owner Pricing Sandbox Apply Output ---")
            print(f"Sandbox output: {args.output}")
            if args.summary_report:
                print(f"Summary report: {args.summary_report}")
            if args.summary_json:
                print(f"Summary JSON: {args.summary_json}")
            print(f"CSV rows read: {result.rows_read}")
            print(f"Valid rows applied: {result.valid_rows}")
            print(f"Invalid rows skipped: {result.invalid_rows}")
            print(f"Added materials: {result.added_materials}")
            print(f"Updated materials: {result.updated_materials}")
            print(f"Unchanged materials: {result.unchanged_materials}")
            print(f"Duplicate keys: {result.duplicate_material_keys}")
            print(f"Sandbox materials written: {result.sandbox_materials_written}")
        elif args.command in (
            "owner-pricing-approve-sandbox-output",
            "owner-pricing-approval-gate",
        ):
            import sys
            from .owner_pricing import write_owner_pricing_approval_record
            try:
                result = write_owner_pricing_approval_record(
                    sandbox_output_path=args.sandbox_output,
                    sandbox_apply_plan_path=args.sandbox_apply_plan,
                    dry_run_report_path=args.dry_run_report,
                    owner_approval=args.owner_approval,
                    approved_by=args.approved_by,
                    approval_record_path=args.approval_record,
                    markdown_summary_path=args.markdown_summary,
                    overwrite=args.overwrite,
                )
            except Exception as e:
                print(f"Error: {str(e)}", file=sys.stderr)
                raise SystemExit(1)

            print("\n--- Owner Pricing Approval Gate ---")
            print(f"Approval record: {args.approval_record}")
            if args.markdown_summary:
                print(f"Markdown summary: {args.markdown_summary}")
            print(f"Sandbox output: {args.sandbox_output}")
            print(f"Sandbox output SHA-256: {result.sandbox_output_sha256}")
            print(f"Approved by: {result.approved_by}")
            print("Final import enabled: false")
            print("Live JSON mutated: false")
            print("Production pricing mutated: false")
        elif args.command in (
            "owner-pricing-final-import-preflight",
            "owner-pricing-preflight-final-import",
        ):
            import sys
            from .owner_pricing import write_owner_pricing_final_import_preflight
            try:
                result = write_owner_pricing_final_import_preflight(
                    sandbox_output_path=args.sandbox_output,
                    approval_record_path=args.approval_record,
                    production_target_path=args.production_target,
                    backup_output_path=args.backup_output,
                    report_path=args.report,
                    report_json_path=args.report_json,
                    overwrite=args.overwrite,
                )
            except Exception as e:
                print(f"Error: {str(e)}", file=sys.stderr)
                raise SystemExit(1)

            print("\n--- Owner Pricing Final Import Preflight ---")
            print(f"Status: {'PASS' if result.passed else 'FAIL'}")
            print(f"Report: {args.report}")
            if args.report_json:
                print(f"Report JSON: {args.report_json}")
            print(f"Sandbox output SHA-256: {result.sandbox_output_sha256}")
            print(f"Approval record SHA-256: {result.approval_record_sha256}")
            print(f"Production target SHA-256: {result.production_target_sha256}")
            print("No final import command invoked.")
            print("No production write performed.")
        elif args.command == "owner-pricing-final-import-fake-rehearsal":
            import sys
            from .owner_pricing import run_owner_pricing_final_import_fake_rehearsal
            try:
                result = run_owner_pricing_final_import_fake_rehearsal(
                    sandbox_output_path=args.sandbox_output,
                    approval_record_path=args.approval_record,
                    preflight_report_path=args.preflight_report,
                    fake_production_target_path=args.fake_production_target,
                    fake_production_output_path=args.fake_production_output,
                    backup_output_path=args.backup_output,
                    audit_log_path=args.audit_log,
                    report_path=args.report,
                    overwrite=args.overwrite,
                    simulate_post_write_validation_failure=args.simulate_post_write_validation_failure,
                    simulate_rollback_verification_failure=args.simulate_rollback_verification_failure,
                )
            except Exception as e:
                print(f"Error: {str(e)}", file=sys.stderr)
                raise SystemExit(1)

            print("\n--- Owner Pricing Final Import Fake Rehearsal ---")
            print(f"Status: {result.status}")
            print(f"Report: {result.report_path}")
            print(f"Audit log: {result.audit_log_path}")
            print(f"Fake production output: {result.fake_production_output_path}")
            print(f"Fake backup output: {result.backup_output_path}")
            print(f"Sandbox output SHA-256: {result.sandbox_output_sha256}")
            print(f"Approval record SHA-256: {result.approval_record_sha256}")
            print(f"Preflight report SHA-256: {result.preflight_report_sha256}")
            print("Fake-fixture-only rehearsal.")
            print("No real production import command invoked.")
            print("No real production write performed.")
        else:
            parser.print_help()
    except Exception as e:
        if args.debug:
            logger.exception("An error occurred during execution.")
        else:
            logger.error(f"Error: {str(e)}. Use --debug for more details.")

if __name__ == "__main__":
    main()
