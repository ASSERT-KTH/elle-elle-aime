from ..text.instruct import InstructEvaluationStrategy
from elleelleaime.core.benchmarks.bug import Bug

from typing import Optional, List


class OpenAIEvaluationStrategy(InstructEvaluationStrategy):

    def __init__(self, **kwargs):
        super().__init__(kwargs=kwargs)

    def _evaluate_impl(self, bug: Bug, sample: dict) -> Optional[List[dict]]:
        """
        Returns the evaluation for the given bug and sample.

        :param bug: The bug to generate the prompt for.
        :param sample: The sample to evaluate.
        """
        evaluation = []

        if sample["generation"] is None:
            return evaluation

        for choice in sample["generation"]["choices"]:
            message = choice["message"]["content"]
            candidate_patch = self.extract_patch_from_message(message)
            evaluation.append(self.evaluate_generation(bug, sample, candidate_patch))

        return evaluation
