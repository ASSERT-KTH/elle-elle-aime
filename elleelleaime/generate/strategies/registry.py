from elleelleaime.generate.strategies.strategy import PatchGenerationStrategy
from elleelleaime.generate.strategies.models.openai.openai import (
    OpenAIChatCompletionModels,
)
from elleelleaime.generate.strategies.models.huggingface.incoder import (
    IncoderHFModels,
)
from elleelleaime.generate.strategies.models.huggingface.codellama import (
    CodeLlamaHFModels,
)
from elleelleaime.generate.strategies.models.huggingface.starcoder import (
    StarCoderHFModels,
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
        "incoder-1b": (IncoderHFModels, ("facebook/incoder-1B",)),
        "incoder-6b": (IncoderHFModels, ("facebook/incoder-6B",)),
        "codellama-7b": (CodeLlamaHFModels, ("codellama/CodeLlama-7b-hf",)),
        "codellama-13b": (CodeLlamaHFModels, ("codellama/CodeLlama-13b-hf",)),
        "codellama-7b-instruct": (
            CodeLlamaHFModels,
            ("codellama/CodeLlama-7b-Instruct-hf",),
        ),
        "codellama-13b-instruct": (
            CodeLlamaHFModels,
            ("codellama/CodeLlama-13b-Instruct-hf",),
        ),
        "starcoderbase": (
            StarCoderHFModels,
            ("bigcode/starcoderbase",),
        ),
        "starcoder": (
            StarCoderHFModels,
            ("bigcode/starcoder",),
        ),
        "starcoderplus": (
            StarCoderHFModels,
            ("bigcode/starcoderplus",),
        ),
        "starcoderbase-1b": (
            StarCoderHFModels,
            ("bigcode/starcoderbase-1b",),
        ),
        "starcoderbase-3b": (
            StarCoderHFModels,
            ("bigcode/starcoderbase-3b",),
        ),
        "starcoderbase-7b": (
            StarCoderHFModels,
            ("bigcode/starcoderbase-7b",),
        ),
    }

    @classmethod
    def get_generation(cls, name: str, **kwargs) -> PatchGenerationStrategy:
        if name.lower().strip() not in cls.__MODELS:
            raise ValueError(f"Unknown model {name}")
        model_class, model_args = cls.__MODELS[name.lower().strip()]
        return model_class(*model_args, **kwargs)
