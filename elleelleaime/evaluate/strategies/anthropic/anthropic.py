from ..text.instruct import InstructEvaluationStrategy
from elleelleaime.core.benchmarks.bug import Bug

from typing import Optional, List


class AnthropicEvaluationStrategy(InstructEvaluationStrategy):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __evaluate_generation(self, bug: Bug, sample: dict, generation) -> List[dict]:
        """
        Evaluate the generation for the given bug.

        :param bug: The bug to generate the prompt for.
        :param generation: The generation to evaluate
        """
        evaluation = []

        for content in generation["content"]:
            message = content["text"]
            candidate_patch = self.extract_patch_from_message(message)
            evaluation.append(self.evaluate_generation(bug, sample, candidate_patch))

        return evaluation

    def _evaluate_impl(self, bug: Bug, sample: dict) -> Optional[List[dict]]:
        """
        Returns the evaluation for the given bug and sample.

        :param bug: The bug to generate the prompt for.
        :param sample: The sample to evaluate.
        """
        evaluation = []

        if sample["generation"] is None:
            return evaluation

        for generation in sample["generation"]:
            evaluation.extend(self.__evaluate_generation(bug, sample, generation))

        return evaluation
