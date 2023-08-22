from generate.strategies.strategy import PatchGenerationStrategy
from generate.strategies.models.openai import OpenAIChatCompletionModels
from generate.strategies.models.alvis import AlvisHFModels


class PatchGenerationStrategyRegistry:
    """
    Class for storing and retrieving models based on their name.
    """

    def __init__(self, **kwargs):
        self._models: dict[str, PatchGenerationStrategy] = {
            "gpt-3.5-turbo": OpenAIChatCompletionModels("gpt-3.5-turbo", **kwargs),
            "incoder-1b": AlvisHFModels("facebook/incoder-1B", **kwargs),
            "incoder-6b": AlvisHFModels("facebook/incoder-6B", **kwargs),
        }

    def get_generation(self, name: str) -> PatchGenerationStrategy:
        if name.lower().strip() not in self._models:
            raise ValueError(f"Unknown model {name}")
        return self._models[name.lower().strip()]
