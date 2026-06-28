import logging
from typing import List, Dict, Any, Optional
from .base import BaseProvider, ProviderProfile

logger = logging.getLogger(__name__)

class GenericMockProvider(BaseProvider):
    def __init__(self, profile: ProviderProfile):
        self.profile = profile

    def generate_mock_result(self, brief: Any) -> Dict[str, Any]:
        logger.info(f"[{self.profile.name}] Generating mock result for task...")
        return {
            "status": "success",
            "provider": self.profile.name,
            "message": "This is a mock generation result."
        }

class ProviderRegistry:
    _instance = None
    _providers: Dict[str, BaseProvider] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProviderRegistry, cls).__new__(cls)
            cls._instance._load_default_providers()
        return cls._instance

    def _load_default_providers(self):
        # In a real app, this might load from config/provider_profiles.default.json
        profiles = [
            ProviderProfile(
                name="OpenAI",
                supported_tasks=["image"],
                unsupported_tasks=["video", "audio", "3d"],
                strengths=["versatility", "prompt adherence"],
                weaknesses=["photorealism sometimes plastic", "text rendering in images can be hit or miss"],
                quality_level=4,
                speed_level=4,
                cost_level=3,
                risk_notes="Might over-censor certain prompts.",
                suited_usage="General purpose conceptual art.",
                unsuited_usage="Hyper-realistic human faces."
            ),
            ProviderProfile(
                name="Runway",
                supported_tasks=["video"],
                unsupported_tasks=["image", "audio", "ui"],
                strengths=["gen2 video synthesis", "high-end aesthetics"],
                weaknesses=["high cost", "generation time can be slow"],
                quality_level=4,
                speed_level=3,
                cost_level=4,
                risk_notes="Output can sometimes morph unpredictably.",
                suited_usage="Cinematic B-roll generation.",
                unsuited_usage="Precise instructional videos."
            ),
            ProviderProfile(
                name="Veo",
                supported_tasks=["video"],
                unsupported_tasks=["image", "ui"],
                strengths=["hyper-realistic", "long consistency"],
                weaknesses=["extremely expensive", "very slow"],
                quality_level=5,
                speed_level=2,
                cost_level=5,
                risk_notes="High budget burn rate.",
                suited_usage="High-budget film trailers.",
                unsuited_usage="Quick social media shorts."
            ),
            ProviderProfile(
                name="Fal.ai",
                supported_tasks=["image", "video"],
                unsupported_tasks=["ui", "3d"],
                strengths=["blazing fast inference", "good for bulk operations"],
                weaknesses=["quality can fluctuate", "requires precise prompts"],
                quality_level=3,
                speed_level=5,
                cost_level=2,
                risk_notes="API stability during peak hours.",
                suited_usage="Real-time or bulk generation.",
                unsuited_usage="Final polish high-res masterpieces."
            ),
            ProviderProfile(
                name="Leonardo.ai",
                supported_tasks=["image", "ui", "character"],
                unsupported_tasks=["video"],
                strengths=["game assets", "ui elements", "consistent styles"],
                weaknesses=["needs negative prompts tuning"],
                quality_level=4,
                speed_level=3,
                cost_level=2,
                risk_notes="Style bleeding across elements.",
                suited_usage="Game dev asset pipelines.",
                unsuited_usage="Photographic product shots."
            ),
            ProviderProfile(
                name="MockProvider",
                supported_tasks=["image", "video", "ui", "character", "audio", "3d"],
                unsupported_tasks=[],
                strengths=["free", "instant"],
                weaknesses=["not real output"],
                quality_level=3,
                speed_level=5,
                cost_level=1,
                risk_notes="Outputs are completely fake.",
                suited_usage="Unit testing.",
                unsuited_usage="Production."
            )
        ]
        
        for profile in profiles:
            self.register(GenericMockProvider(profile))

    def register(self, provider: BaseProvider):
        self._providers[provider.name.lower()] = provider
        logger.debug(f"Registered provider: {provider.name}")

    @classmethod
    def get(cls, name: str) -> Optional[BaseProvider]:
        registry = cls()
        return registry._providers.get(name.lower())

    @classmethod
    def list_all(cls) -> List[BaseProvider]:
        registry = cls()
        return list(registry._providers.values())
