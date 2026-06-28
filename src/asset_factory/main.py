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
        else:
            parser.print_help()
    except Exception as e:
        if args.debug:
            logger.exception("An error occurred during execution.")
        else:
            logger.error(f"Error: {str(e)}. Use --debug for more details.")

if __name__ == "__main__":
    main()
