from elleelleaime.generate.strategies.strategy import PatchGenerationStrategy
from elleelleaime.generate.strategies.models.openai.openai import (
    OpenAIChatCompletionModels,
)
from elleelleaime.generate.strategies.models.huggingface.codellama import (
    CodeLlamaHFModels,
)

from typing import Tuple


class PatchGenerationStrategyRegistry:
    """
    Class for storing and retrieving models based on their name.
    """

    # The registry is a dictionary of model names to a tuple of the model class and the model's constructor arguments
    # NOTE: Do not instantiate the model here, as we should only instanciate the class to be used
    __MODELS: dict[str, Tuple[type, Tuple]] = {
        # OpenAI models
        "gpt-3.5-turbo": (OpenAIChatCompletionModels, ("gpt-3.5-turbo",)),
        "gpt-4o-mini": (OpenAIChatCompletionModels, ("gpt-4o-mini",)),
        # HuggingFace models
        "codellama-7b": (CodeLlamaHFModels, ("codellama/CodeLlama-7b-hf",)),
        "codellama-13b": (CodeLlamaHFModels, ("codellama/CodeLlama-13b-hf",)),
    }

    @classmethod
    def get_generation(cls, name: str, **kwargs) -> PatchGenerationStrategy:
        if name.lower().strip() not in cls.__MODELS:
            raise ValueError(f"Unknown model {name}")
        model_class, model_args = cls.__MODELS[name.lower().strip()]
        return model_class(*model_args, **kwargs)
