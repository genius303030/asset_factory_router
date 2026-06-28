import os
import json
import logging
from typing import Dict, Any
from .models import AssetPack
import dataclasses

logger = logging.getLogger(__name__)

class AssetPackWriter:
    @staticmethod
    def write(pack: AssetPack, output_dir: str):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        try:
            # 1. project_brief.json
            with open(os.path.join(output_dir, "project_brief.json"), "w", encoding="utf-8") as f:
                json.dump(dataclasses.asdict(pack.project_brief), f, ensure_ascii=False, indent=2)

            # 2. prompt_pack.md
            with open(os.path.join(output_dir, "prompt_pack.md"), "w", encoding="utf-8") as f:
                f.write(pack.prompt_pack_md)

            # 3. image_prompts.json
            with open(os.path.join(output_dir, "image_prompts.json"), "w", encoding="utf-8") as f:
                json.dump(pack.image_prompts, f, ensure_ascii=False, indent=2)

            # 4. ui_style_guide.md
            with open(os.path.join(output_dir, "ui_style_guide.md"), "w", encoding="utf-8") as f:
                f.write(pack.ui_style_guide_md)

            # 5. storyboard.md
            with open(os.path.join(output_dir, "storyboard.md"), "w", encoding="utf-8") as f:
                f.write(pack.storyboard_md)

            # 6. asset_manifest.json
            with open(os.path.join(output_dir, "asset_manifest.json"), "w", encoding="utf-8") as f:
                json.dump(pack.asset_manifest, f, ensure_ascii=False, indent=2)

            # 7. routing_plan.json
            with open(os.path.join(output_dir, "routing_plan.json"), "w", encoding="utf-8") as f:
                json.dump(dataclasses.asdict(pack.routing_plan), f, ensure_ascii=False, indent=2)

            # 8. codex_asset_tasks.md
            if hasattr(pack, "codex_task_md"):
                with open(os.path.join(output_dir, "codex_asset_tasks.md"), "w", encoding="utf-8") as f:
                    f.write(pack.codex_task_md)

            # 9. production_checklist.md
            if hasattr(pack, "production_checklist_md"):
                with open(os.path.join(output_dir, "production_checklist.md"), "w", encoding="utf-8") as f:
                    f.write(pack.production_checklist_md)

            # 10. pack_summary.md
            if hasattr(pack, "pack_summary_md"):
                with open(os.path.join(output_dir, "pack_summary.md"), "w", encoding="utf-8") as f:
                    f.write(pack.pack_summary_md)

            logger.info(f"Asset Pack successfully written to {output_dir}")
        except Exception as e:
            logger.error(f"Failed to write Asset Pack: {e}", exc_info=True)
            raise
