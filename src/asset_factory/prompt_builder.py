from typing import Dict, List, Any
from .models import ProjectBrief

class PromptBuilder:
    @staticmethod
    def build_prompt_pack(brief: ProjectBrief) -> str:
        md = f"# Prompt Pack: {brief.project_name}\n\n"
        md += f"## Master Description\n{brief.description}\n\n"
        md += "## Context\n"
        md += f"- **Target Audience**: {brief.target_audience}\n"
        md += f"- **Style**: {brief.style}\n\n"
        md += "## Generation Prompts\n"
        md += "Use the prompts in `image_prompts.json` for image generation models.\n"
        return md

    @staticmethod
    def build_image_prompts(brief: ProjectBrief) -> List[Dict[str, str]]:
        prompts = []
        base_prompt = f"{brief.description}, style of {brief.style}, high quality"
        
        prompts.append({
            "id": "img_001",
            "type": "main_concept",
            "prompt": f"Main concept art: {base_prompt}, masterpiece, 8k resolution, trending on artstation."
        })
        
        if brief.task_type == "ui":
            prompts.append({
                "id": "ui_001",
                "type": "ui_layout",
                "prompt": f"UI Layout design for {brief.project_name}, {brief.style}, clear typography, modern layout, vector style."
            })
            
        return prompts

    @staticmethod
    def build_ui_style_guide(brief: ProjectBrief) -> str:
        if brief.task_type != "ui":
            return "# UI Style Guide\n\nN/A - This project is not primarily UI focused."
            
        md = f"# UI Style Guide: {brief.project_name}\n\n"
        md += f"**Core Theme**: {brief.style}\n\n"
        md += "## Colors\n- Primary: TBD\n- Secondary: TBD\n- Accent: TBD\n\n"
        md += "## Typography\n- Headers: Modern Sans-Serif\n- Body: Readable Sans-Serif\n"
        return md

    @staticmethod
    def build_storyboard(brief: ProjectBrief) -> str:
        if brief.task_type != "video":
            return "# Storyboard\n\nN/A - This project is not a video task."
            
        md = f"# Storyboard: {brief.project_name}\n\n"
        md += "## Scene 1: Introduction\n"
        md += f"**Visual**: Establishing shot matching: {brief.description}\n"
        md += "**Audio**: Ambient intro music.\n\n"
        md += "## Scene 2: Main Feature\n"
        md += "**Visual**: Close up on core elements.\n"
        md += "**Audio**: Whoosh sound effect.\n"
        return md
