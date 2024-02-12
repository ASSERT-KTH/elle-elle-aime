from typing import Optional, Tuple, Union
from unidiff import PatchSet

from elleelleaime.sample.prompting.strategy import PromptingStrategy
from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.utils.java_tools.java import extract_single_function


class FunctionToFunctionPrompting(PromptingStrategy):
    """
    Implements the function-to-function style prompt strategy.
    """

    def __init__(self, **kwargs):
        super().__init__("function-to-function")

        self.model_name: str = kwargs.get("model_name", "").strip().lower()
        # TODO: add_fault_localization

    def function_to_function(
        self, bug: Bug
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Builds a function-to-function prompt for the given bug.

        Args:
            bug: The bug to generate the prompt for.
        Returns:
            Tuple: A tuple of the form (buggy_code, fixed_code, prompt).
        """
        result = extract_single_function(bug)
        if result is None:
            return None, None, None

        buggy_code, fixed_code = result

        # TODO: add fault localization option
        prompt = buggy_code

        return buggy_code, fixed_code, prompt

    def prompt(self, bug: Bug) -> dict[str, Optional[str]]:
        """
        Returns the prompt for the given bug.

        :param bug: The bug to generate the prompt for.
        """
        result = {
            "identifier": bug.get_identifier(),
            "buggy_code": None,
            "fixed_code": None,
            "prompt_strategy": self.strategy_name,
            "prompt": None,
            "ground_truth": bug.get_ground_truth(),
        }

        diff = PatchSet(bug.get_ground_truth())
        # This strategy only supports single-file prompts
        if len(diff) != 1:
            return result

        (
            result["buggy_code"],
            result["fixed_code"],
            result["prompt"],
        ) = self.function_to_function(bug)
        return result
