from abc import ABC, abstractmethod

from typing import Optional, List


class MufinProcessStrategy(ABC):
    def __init__(self, strategy_name: str, **kwargs):
        self.strategy_name = strategy_name

    @abstractmethod
    def process(self, bug: dict[str, Optional[str]]) -> List[dict[str, Optional[str]]]:
        """
        Processes the bug and returns a list of samples.
        """
        pass
