import os
import json
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class PackInspector:
    EXPECTED_FILES = [
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

    @staticmethod
    def inspect(pack_dir: str) -> Dict[str, Any]:
        result = {
            "status": "Ready",
            "missing_files": [],
            "warnings": [],
            "can_proceed": True,
            "next_steps": "Hand off to production team or Codex."
        }

        if not os.path.exists(pack_dir) or not os.path.isdir(pack_dir):
            result["status"] = "Invalid Directory"
            result["can_proceed"] = False
            result["warnings"].append(f"Directory not found: {pack_dir}")
            return result

        # Check expected files
        for f in PackInspector.EXPECTED_FILES:
            filepath = os.path.join(pack_dir, f)
            if not os.path.exists(filepath):
                result["missing_files"].append(f)
                result["can_proceed"] = False
                result["status"] = "Incomplete"
            else:
                # Check file size
                if os.path.getsize(filepath) == 0:
                    result["warnings"].append(f"File is empty: {f}")

        # Check JSON parseability
        json_files = ["project_brief.json", "image_prompts.json", "asset_manifest.json", "routing_plan.json"]
        for jf in json_files:
            filepath = os.path.join(pack_dir, jf)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        json.load(f)
                except json.JSONDecodeError:
                    result["warnings"].append(f"File {jf} is not valid JSON.")
                    result["can_proceed"] = False
                    result["status"] = "Corrupt"
                except Exception as e:
                    result["warnings"].append(f"Could not read {jf}: {e}")

        if not result["can_proceed"]:
            result["next_steps"] = "Fix missing or corrupt files before handing off."

        return result
