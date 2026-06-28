from typing import List, Dict, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

@dataclass
class ProviderProfile:
    name: str
    supported_tasks: List[str]
    unsupported_tasks: List[str]
    strengths: List[str]
    weaknesses: List[str]
    quality_level: int # 1-5
    speed_level: int   # 1-5
    cost_level: int    # 1-5
    risk_notes: str
    suited_usage: str
    unsuited_usage: str

class BaseProvider(ABC):
    profile: ProviderProfile

    @property
    def name(self) -> str: return self.profile.name
    @property
    def supported_tasks(self) -> List[str]: return self.profile.supported_tasks
    @property
    def strengths(self) -> List[str]: return self.profile.strengths
    @property
    def weaknesses(self) -> List[str]: return self.profile.weaknesses
    @property
    def quality_level(self) -> int: return self.profile.quality_level
    @property
    def speed_level(self) -> int: return self.profile.speed_level
    @property
    def cost_level(self) -> int: return self.profile.cost_level

    @abstractmethod
    def generate_mock_result(self, brief: Any) -> Dict[str, Any]:
        """Generate a mock result based on the provided brief."""
        pass
