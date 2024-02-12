from abc import ABC, abstractmethod
from elleelleaime.core.benchmarks.bug import Bug

from typing import Optional, Union, List


class MufinStrategy(ABC):
    def __init__(self, strategy_name: str, **kwargs):
        self.strategy_name = strategy_name

    @abstractmethod
    def sample(self, bug: Bug) -> List[dict[str, Optional[Union[str, Bug]]]]:
        """
        Returns a list of samples for each bug.

        :param bug: The bug to generate samples from.
        :return: A list of dictionaries containing the samples and other relevant information.
        """
        pass
