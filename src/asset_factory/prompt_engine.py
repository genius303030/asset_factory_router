import os
import logging
from typing import Dict, Any
from .models import RoutingPlan

logger = logging.getLogger(__name__)

class PromptEngine:
    @staticmethod
    def load_template(filename: str) -> str:
        template_path = os.path.join(os.path.dirname(__file__), "prompt_templates", filename)
        if not os.path.exists(template_path):
            logger.warning(f"Template {filename} not found, using fallback.")
            return f"[{filename} not found]"
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def generate_prompt_pack(brief: Dict[str, Any], routing_plan: RoutingPlan) -> str:
        # Load templates
        main_tpl = PromptEngine.load_template("prompt_pack_template.md")
        img_tpl = PromptEngine.load_template("image_prompt_template.md")
        ui_tpl = PromptEngine.load_template("ui_style_template.md")
        story_tpl = PromptEngine.load_template("storyboard_template.md")
        codex_tpl = PromptEngine.load_template("codex_task_template.md")
        neg_tpl = PromptEngine.load_template("negative_prompt_template.md")
        route_tpl = PromptEngine.load_template("routing_notes_template.md")

        # Format variables
        p_name = brief.get("project_name", "Untitled")
        desc = brief.get("description", "")
        task_type = brief.get("task_type", "unknown")
        style = brief.get("style", "generic")
        aud = brief.get("audience", "general")
        usage = brief.get("usage_context", "unknown")
        qual = brief.get("quality", "medium")
        speed = brief.get("speed", "normal")
        budget = brief.get("budget", "medium")
        outputs = brief.get("target_outputs", [])
        
        # Sub-templates
        img_content = img_tpl.format(style=style, description=desc, quality=qual, audience=aud)
        ui_content = ui_tpl.format(style=style, quality=qual, usage_context=usage)
        story_content = story_tpl.format(description=desc, task_type=task_type, style=style, audience=aud)
        codex_content = codex_tpl.format(style=style, usage_context=usage)
        neg_content = neg_tpl.format(style=style)
        route_content = route_tpl.format(
            recommended_provider=routing_plan.recommended_provider,
            fallback_provider=routing_plan.fallback_provider,
            reason=routing_plan.reason,
            risk_notes=routing_plan.risk_notes
        )

        # Main merge
        prompt_pack = main_tpl.format(
            project_name=p_name,
            description=desc,
            task_type=task_type,
            style=style,
            audience=aud,
            usage_context=usage,
            quality=qual,
            speed=speed,
            budget=budget,
            negative_keywords="blur, ugly, lowres",
            image_prompts=img_content,
            ui_style=ui_content,
            storyboard=story_content,
            routing_notes=route_content,
            codex_notes=codex_content,
            negative_prompts=neg_content,
            output_count=len(outputs),
            target_outputs=", ".join(outputs),
            recommended_provider=routing_plan.recommended_provider
        )
        return prompt_pack

    @staticmethod
    def generate_image_prompts_json(brief: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "primary": f"A highly detailed {brief.get('style')} image of {brief.get('description')}",
            "variations": [
                f"Wide angle, {brief.get('audience')} context",
                f"Close up, {brief.get('style')} emphasis"
            ]
        }

    @staticmethod
    def generate_storyboard(brief: Dict[str, Any]) -> str:
        story_tpl = PromptEngine.load_template("storyboard_template.md")
        return story_tpl.format(
            description=brief.get("description", ""),
            task_type=brief.get("task_type", ""),
            style=brief.get("style", ""),
            audience=brief.get("audience", "")
        )

    @staticmethod
    def generate_ui_style_guide(brief: Dict[str, Any]) -> str:
        ui_tpl = PromptEngine.load_template("ui_style_template.md")
        return ui_tpl.format(
            style=brief.get("style", ""),
            quality=brief.get("quality", ""),
            usage_context=brief.get("usage_context", "")
        )

    @staticmethod
    def build_codex_task(brief: Any) -> str:
        # Wrapper for consistency with main.py
        tpl = PromptEngine.load_template("codex_task_template.md")
        # In main, brief is a dataclass, so we use getattr
        style = getattr(brief, 'style', 'generic')
        usage = getattr(brief, 'usage_context', 'unknown')
        return tpl.format(style=style, usage_context=usage)

    @staticmethod
    def build_production_checklist(brief: Any) -> str:
        return f"""# Production Checklist: {getattr(brief, 'project_name', 'Untitled')}
- [ ] Review Prompt Pack and Route Plan
- [ ] Ensure API keys or local instances are ready
- [ ] Validate output specs (Target: {', '.join(getattr(brief, 'target_outputs', []))})
- [ ] Proceed to generation phase
"""

    @staticmethod
    def build_pack_summary(brief: Any, routing_plan: RoutingPlan) -> str:
        return f"""# Pack Summary
This Asset Pack was generated for the project: **{getattr(brief, 'project_name', 'Untitled')}**.
It targets the **{getattr(brief, 'task_type', 'unknown')}** domain using a **{getattr(brief, 'style', 'generic')}** style.
We recommend using **{routing_plan.recommended_provider}** for generation.

**Next step:** Pass this directory to Codex or your production pipeline.
"""
