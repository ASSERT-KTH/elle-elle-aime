from abc import ABC, abstractmethod
from elleelleaime.core.benchmarks.bug import Bug

from typing import Optional, Union


class PromptingStrategy(ABC):
    def __init__(self, strategy_name: str, **kwargs):
        self.strategy_name = strategy_name

    @abstractmethod
    def prompt(self, bug: Bug) -> dict[str, Optional[Union[str, Bug]]]:
        """
        Returns the prompt for the given bug.

        :param bug: The bug to generate the prompt for.
        :return: A dictionary containing the prompt and other relevant information.
        """
        pass
