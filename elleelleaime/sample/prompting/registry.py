from .strategy import PromptingStrategy
from .strategies.zero_shot_cloze import ZeroShotClozePrompting
from .strategies.fill_in_the_middle import FillInTheMiddlePrompting
from .strategies.function_to_function import FunctionToFunctionPrompting
from .strategies.instruct import InstructPrompting


class PromptStrategyRegistry:
    """
    Class for storing and retrieving prompting strategies based on their name.
    """

    __STRATEGIES: dict[str, type] = {
        "zero-shot-cloze": ZeroShotClozePrompting,
        "fill-in-the-middle": FillInTheMiddlePrompting,
        "function-to-function": FunctionToFunctionPrompting,
        "instruct": InstructPrompting,
    }

    @classmethod
    def get_strategy(cls, name: str, **kwargs) -> PromptingStrategy:
        if name.lower().strip() not in cls.__STRATEGIES:
            raise ValueError(f"Unknown prompting strategy {name}")
        return cls.__STRATEGIES[name.lower().strip()](**kwargs)
