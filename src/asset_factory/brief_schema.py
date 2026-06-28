from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class BriefSchema:
    project_name: str
    description: str
    target_outputs: List[str]
    style: str
    quality: str
    budget: str
    task_type: str
    audience: str
    usage_context: str
    additional_notes: Optional[str] = None
    batch_size: str = "medium"
    speed: str = "normal"

    @classmethod
    def get_required_fields(cls) -> List[str]:
        return [
            "project_name", "description", "target_outputs", "style", 
            "quality", "budget", "task_type", "audience", "usage_context"
        ]

    @classmethod
    def get_allowed_values(cls) -> Dict[str, List[str]]:
        return {
            "quality": ["low", "medium", "high", "ultra"],
            "budget": ["low", "medium", "high"],
            "task_type": ["image", "video", "ui", "audio", "3d", "character"],
            "speed": ["slow", "normal", "fast"],
            "batch_size": ["small", "medium", "large"]
        }
