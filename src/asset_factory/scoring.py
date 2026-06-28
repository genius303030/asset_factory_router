import os
import json
import logging
from typing import Dict, Any, Tuple
from .providers.base import BaseProvider

logger = logging.getLogger(__name__)

class ConfiguredScoringSystem:
    DEFAULT_CONFIG = {
        "quality_weight": {"low": 1.0, "medium": 3.0, "high": 5.0},
        "speed_weight": {"slow": 1.0, "normal": 3.0, "fast": 5.0},
        "budget_weight": {"low": 5.0, "medium": 3.0, "high": 1.0},
        "style_bonus": 10.0,
        "batch_size_modifier": {"small": 1.0, "medium": 1.0, "large": 2.0},
        "task_type_priority": {"image": 1.0, "video": 1.5, "ui": 1.2},
        "provider_penalty": {"MockProvider": -50.0},
        "fallback_threshold": 0.0
    }

    @classmethod
    def load_config(cls) -> Tuple[Dict[str, Any], str]:
        config_path = os.path.join(os.getcwd(), "config", "router_weights.json")
        default_path = os.path.join(os.getcwd(), "config", "router_weights.default.json")
        
        target_path = config_path if os.path.exists(config_path) else default_path
        
        if not os.path.exists(target_path):
            logger.warning("No config files found. Using hardcoded defaults.")
            return cls.DEFAULT_CONFIG, "hardcoded_default"

        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config, os.path.basename(target_path)
        except Exception as e:
            logger.error(f"Failed to load config: {e}. Using hardcoded defaults.")
            return cls.DEFAULT_CONFIG, "hardcoded_default_on_error"

    @classmethod
    def calculate_score(cls, provider: BaseProvider, brief_data: Dict[str, str], config: Dict[str, Any] = None) -> Tuple[float, Dict[str, float]]:
        if config is None:
            config, _ = cls.load_config()

        breakdown = {
            "quality": 0.0,
            "speed": 0.0,
            "cost": 0.0,
            "style_match": 0.0,
            "task_support": 0.0,
            "batch_size": 0.0,
            "risk_penalty": 0.0,
            "provider_penalty": 0.0
        }

        # Base requirement: Task Support
        if brief_data.get("task_type") not in provider.supported_tasks:
            breakdown["task_support"] = -1000.0
            return -1.0, breakdown
        else:
            breakdown["task_support"] = 10.0 # base points for supporting it

        score = breakdown["task_support"]

        # Style match
        style = brief_data.get("style", "")
        if style:
            for st in provider.strengths:
                if style.lower() in st.lower() or st.lower() in style.lower():
                    breakdown["style_match"] += config.get("style_bonus", 10.0)
        score += breakdown["style_match"]

        # Quality
        req_quality = brief_data.get("quality", "medium")
        q_weight = config.get("quality_weight", cls.DEFAULT_CONFIG["quality_weight"]).get(req_quality, 3.0)
        breakdown["quality"] = provider.quality_level * q_weight
        score += breakdown["quality"]

        # Speed
        req_speed = brief_data.get("speed", "normal")
        s_weight = config.get("speed_weight", cls.DEFAULT_CONFIG["speed_weight"]).get(req_speed, 3.0)
        breakdown["speed"] = provider.speed_level * s_weight
        score += breakdown["speed"]

        # Cost
        req_budget = brief_data.get("budget", "medium")
        b_weight = config.get("budget_weight", cls.DEFAULT_CONFIG["budget_weight"]).get(req_budget, 3.0)
        inverted_cost = 6 - provider.cost_level
        breakdown["cost"] = inverted_cost * b_weight
        score += breakdown["cost"]

        # Provider penalty
        penalty = config.get("provider_penalty", {}).get(provider.name, 0.0)
        breakdown["provider_penalty"] = penalty
        score += breakdown["provider_penalty"]

        # Risk penalty (simulate based on length of weaknesses)
        risk_factor = config.get("risk_penalty_factor", 2.0)
        breakdown["risk_penalty"] = -1 * len(provider.weaknesses) * risk_factor
        score += breakdown["risk_penalty"]

        # Batch size modifier
        batch_size = brief_data.get("batch_size", "medium")
        modifier = config.get("batch_size_modifier", {}).get(batch_size, 1.0)
        if batch_size == "large" and provider.cost_level <= 2:
            breakdown["batch_size"] = score * (modifier - 1.0) # difference added
            score *= modifier

        return score, breakdown
