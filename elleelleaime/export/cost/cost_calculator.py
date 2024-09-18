from .strategies.openai import OpenAICostStrategy
from .strategies.google import GoogleCostStrategy
from .strategies.openrouter import OpenRouterCostStrategy

from typing import Optional


class CostCalculator:

    __COST_STRATEGIES = {
        "openai-chatcompletion": OpenAICostStrategy,
        "google": GoogleCostStrategy,
        "openrouter": OpenRouterCostStrategy,
    }

    @staticmethod
    def compute_costs(samples: list, provider: str, model_name: str) -> Optional[dict]:
        strategy = CostCalculator.__COST_STRATEGIES.get(provider)
        if strategy is None:
            return None
        return strategy.compute_costs(samples, model_name)
