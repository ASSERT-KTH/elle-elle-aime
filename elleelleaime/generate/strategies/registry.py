from elleelleaime.generate.strategies.strategy import PatchGenerationStrategy
from elleelleaime.generate.strategies.models.openai.openai import (
    OpenAIChatCompletionModels,
)
from elleelleaime.generate.strategies.models.huggingface.alvis import (
    AlvisHFModels,
)
from elleelleaime.generate.strategies.models.huggingface.incoder import (
    IncoderHFModels,
)


class PatchGenerationStrategyRegistry:
    """
    Class for storing and retrieving models based on their name.
    """

    def __init__(self, **kwargs):
        self._models: dict[str, PatchGenerationStrategy] = {
            "gpt-3.5-turbo": OpenAIChatCompletionModels("gpt-3.5-turbo", **kwargs),
            "incoder-1b": IncoderHFModels("facebook/incoder-1B", **kwargs),
            "incoder-6b": IncoderHFModels("facebook/incoder-6B", **kwargs),
        }

    def get_generation(self, name: str) -> PatchGenerationStrategy:
        if name.lower().strip() not in self._models:
            raise ValueError(f"Unknown model {name}")
        return self._models[name.lower().strip()]
