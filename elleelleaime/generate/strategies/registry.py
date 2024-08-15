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

    # The registry is a dictionary of strategy names to a tuple of the class and the mandatory arguments to pass to the class
    # NOTE: Do not instantiate the model here, as we should only instanciate the class to be used
    __MODELS: dict[str, Tuple[type, Tuple]] = {
        "openai-chatcompletion": (OpenAIChatCompletionModels, ("model_name",)),
        "codellama": (CodeLlamaHFModels, ("model_name",)),
    }

    @classmethod
    def get_generation(cls, name: str, **kwargs) -> PatchGenerationStrategy:
        if name.lower().strip() not in cls.__MODELS:
            raise ValueError(f"Unknown strategy {name}")

        strategy_class, strategy_args = cls.__MODELS[name.lower().strip()]
        for strategy_arg in strategy_args:
            if strategy_arg not in kwargs:
                raise ValueError(f"Missing argument {strategy_arg} for strategy {name}")
        return strategy_class(**kwargs)
