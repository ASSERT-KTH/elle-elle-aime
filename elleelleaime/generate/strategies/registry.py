from generate.strategies.strategy import PatchGenerationStrategy
from generate.strategies.models.openai import OpenAIChatCompletionModels
from generate.strategies.models.alvis import AlvisHFModels

class PatchGenerationStrategyRegistry():
    """
    Class for storing and retrieving models based on their name.
    """
    
    def __init__(self):
        self._models: dict[str, PatchGenerationStrategy] = {
            "gpt-3.5-turbo": OpenAIChatCompletionModels("gpt-3.5-turbo"),
            "incoder-1B-alvis": AlvisHFModels("incoder-1B"),
            "incoder-6B-alvis": AlvisHFModels("incoder-6B"),
        }
        
    def get_generation(self, name: str) -> PatchGenerationStrategy:
        if name.lower().strip() not in self._models:
            raise ValueError(f"Unknown model {name}")
        return self._models[name.lower().strip()]