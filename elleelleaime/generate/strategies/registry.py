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

from typing import Tuple


class PatchGenerationStrategyRegistry:
    """
    Class for storing and retrieving models based on their name.
    """

    def __init__(self, **kwargs):
        # The registry is a dictionary of model names to a tuple of the model class and the model's constructor arguments
        # NOTE: Do not instantiate the model here, as we should only instanciate the class to be used
        self._models: dict[str, Tuple[type, Tuple]] = {
            # OpenAI models
            "gpt-3.5-turbo": (OpenAIChatCompletionModels, ("gpt-3.5-turbo", kwargs)),
            # HuggingFace models
            "incoder-1b": (IncoderHFModels, ("facebook/incoder-1B", kwargs)),
            "incoder-6b": (IncoderHFModels, ("facebook/incoder-6B", kwargs)),
        }

    def get_generation(self, name: str) -> PatchGenerationStrategy:
        if name.lower().strip() not in self._models:
            raise ValueError(f"Unknown model {name}")
        model_class, model_args = self._models[name.lower().strip()]
        return model_class(*model_args)
