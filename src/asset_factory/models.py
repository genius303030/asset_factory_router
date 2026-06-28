import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

@dataclass
class ProjectBrief:
    project_name: str
    task_type: str
    style: str
    quality: str
    speed: str
    budget: str
    batch_size: str
    description: str
    target_audience: str

@dataclass
class RoutingPlan:
    recommended_provider: str
    fallback_provider: str
    all_provider_scores: Dict[str, float]
    score_breakdown: Dict[str, Dict[str, float]]
    reason: str
    risk_notes: str
    estimated_cost_level: str
    estimated_speed_level: str
    selected_config_source: str

@dataclass
class AssetPack:
    project_brief: ProjectBrief
    prompt_pack_md: str
    image_prompts: List[Dict[str, str]]
    ui_style_guide_md: str
    storyboard_md: str
    asset_manifest: Dict[str, Any]
    routing_plan: RoutingPlan
    codex_task_md: str = ""
    production_checklist_md: str = ""
    pack_summary_md: str = ""
