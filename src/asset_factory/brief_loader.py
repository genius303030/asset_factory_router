import json
import os
from .models import ProjectBrief

class BriefLoader:
    @staticmethod
    def load_from_file(file_path: str) -> ProjectBrief:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Brief file not found: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        return ProjectBrief(
            project_name=data.get("project_name", "Untitled Project"),
            task_type=data.get("task_type", "image"),
            style=data.get("style", "realistic"),
            quality=data.get("quality", "medium"),
            speed=data.get("speed", "normal"),
            budget=data.get("budget", "medium"),
            batch_size=data.get("batch_size", "medium"),
            description=data.get("description", ""),
            target_audience=data.get("target_audience", "General")
        )
