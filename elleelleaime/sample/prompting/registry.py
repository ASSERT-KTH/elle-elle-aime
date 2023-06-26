from .strategy import PromptingStrategy
from .strategies.zero_shot_single_hunk import ZeroShotSingleHunkPrompting
from .strategies.zero_shot_cloze import ZeroShotClozePrompting


class PromptStrategyRegistry():
    """
    Class for storing and retrieving prompting strategies based on their name.
    """
    
    def __init__(self):
        self._strategies: dict[str, PromptingStrategy] = {
            "zero-shot-single-hunk": ZeroShotSingleHunkPrompting(),
            "zero-shot-cloze": ZeroShotClozePrompting(),
        }

    def get_strategy(self, name: str) -> PromptingStrategy:
        if name.lower().strip() not in self._strategies:
            raise ValueError(f"Unknown prompting strategy {name}")
        return self._strategies[name.lower().strip()]