from sample.prompting.prompting_strategy import PromptingStrategy
from sample.prompting.strategies.zero_shot_single_hunk import ZeroShotSingleHunkPrompting


class PromptingRegistry():
    """
    Class for storing and retrieving prompting strategies based on their name.
    """
    
    def __init__(self):
        self._strategies: dict[str, PromptingStrategy] = {
            "zero-shot-single-hunk": ZeroShotSingleHunkPrompting(),
        }

    def get_strategy(self, name: str) -> PromptingStrategy:
        return self._strategies[name.lower().strip()]