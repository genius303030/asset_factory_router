import logging
from typing import Dict, Any, List
from .models import RoutingPlan, ProjectBrief
from .providers.base import BaseProvider
from .scoring import ConfiguredScoringSystem

logger = logging.getLogger(__name__)

class ModelRouter:
    @staticmethod
    def generate_routing_plan(task_type: str, style: str, quality: str, speed: str, budget: str) -> RoutingPlan:
        brief_data = {
            "task_type": task_type,
            "style": style,
            "quality": quality,
            "speed": speed,
            "budget": budget
        }

        # Use ProviderRegistry
        from .providers.registry import ProviderRegistry
        real_providers = [p for p in ProviderRegistry.list_all() if p.name != "MockProvider"]
        if not real_providers:
            real_providers = ProviderRegistry.list_all()
        
        config, config_source = ConfiguredScoringSystem.load_config()
        
        scored_providers = []
        all_scores = {}
        breakdowns = {}
        for provider in real_providers:
            score, brk = ConfiguredScoringSystem.calculate_score(provider, brief_data, config)
            all_scores[provider.name] = score
            breakdowns[provider.name] = brk
            logger.debug(f"Provider {provider.name} scored {score}")
            if score >= config.get("fallback_threshold", 0.0) and score != -1.0:
                scored_providers.append((score, provider))

        scored_providers.sort(key=lambda x: x[0], reverse=True)

        if not scored_providers:
            logger.warning("No suitable provider found for this task.")
            return RoutingPlan(
                recommended_provider="None",
                fallback_provider="None",
                all_provider_scores=all_scores,
                score_breakdown=breakdowns,
                reason="No suitable provider found for this task type based on current routing config.",
                estimated_cost_level="N/A",
                estimated_speed_level="N/A",
                risk_notes="Task type might be unsupported or fallback threshold too high.",
                selected_config_source=config_source
            )

        recommended = scored_providers[0][1]
        fallback = scored_providers[1][1] if len(scored_providers) > 1 else recommended

        reason = f"Provider {recommended.name} scored highest ({scored_providers[0][0]}) based on your requirements (Quality: {quality}, Speed: {speed}, Budget: {budget})."
        
        return RoutingPlan(
            recommended_provider=recommended.name,
            fallback_provider=fallback.name,
            all_provider_scores=all_scores,
            score_breakdown=breakdowns,
            reason=reason,
            estimated_cost_level=str(recommended.cost_level),
            estimated_speed_level=str(recommended.speed_level),
            risk_notes=f"Risks to watch out for: {recommended.profile.risk_notes}" if hasattr(recommended, 'profile') else "None",
            selected_config_source=config_source
        )
