from abc import ABC, abstractmethod
from elleelleaime.core.benchmarks.bug import Bug

from typing import Any, List, Optional, final


class PatchEvaluationStrategy(ABC):
    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def _evaluate_impl(self, bug: Bug, sample: dict) -> Optional[List[dict]]:
        """
        Implemenation method for the evaluation strategy.
        """
        pass

    @final
    def _handle_none(self) -> Any:
        """
        Handles the case where the generation is None. For now, we simply return None.
        """
        return None

    @final
    def evaluate(self, bug: Bug, sample: dict) -> Optional[List[dict]]:
        """
        Returns the evaluation results for the given sample.

        :param sample: The sample to evaluate.
        :return: A dictionary containing the evaluation results.
        """
        # Implements the logic common to all generation strategies
        if sample["generation"] is None:
            return self._handle_none()

        return self._evaluate_impl(bug, sample)
