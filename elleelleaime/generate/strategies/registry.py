from .strategy import PatchGenerationStrategy
from .models.openai import OpenAIChatCompletionModels

class PatchGenerationStrategyRegistry():
    """
    Class for storing and retrieving models based on their name.
    """
    
    def __init__(self):
        self._models: dict[str, PatchGenerationStrategy] = {
            "gpt-3.5-turbo": OpenAIChatCompletionModels("gpt-3.5-turbo"),
        }
        
    def get_generation(self, name: str) -> PatchGenerationStrategy:
        if name.lower().strip() not in self._models:
            raise ValueError(f"Unknown model {name}")
        return self._models[name.lower().strip()]