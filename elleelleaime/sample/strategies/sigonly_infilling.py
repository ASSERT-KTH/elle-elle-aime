from typing import Optional, Tuple
from unidiff import PatchSet

from elleelleaime.sample.strategy import PromptingStrategy
from elleelleaime.core.benchmarks.bug import RichBug
from elleelleaime.core.utils.java.java import (
    extract_single_function,
)


class SigOnlyInfillingPrompting(PromptingStrategy):
    """
    Implements function signature only prompting strategies.
    """

    MODEL_DICT = {
        "codellama": {
            "mask_token": "<FILL_ME>",
            "extra_mask_token": False,
            "single_chunk": True,
        },
        # Add the model you want to use here
    }

    def __init__(self, **kwargs):
        super().__init__("sigonly")

        self.model_name: str = kwargs.get("model_name", "").strip().lower()
        assert (
            self.model_name in self.MODEL_DICT.keys()
        ), f"Unknown model name: {kwargs.get('model_name', None)}"
        model_kwargs = self.MODEL_DICT.get(self.model_name, {})
        self.original_mask_token: str = model_kwargs["mask_token"]
        self.extra_mask_token: bool = model_kwargs.get("extra_mask_token", False)

    def function_body_infilling(self, signature: str) -> str:
        return f"{signature} {{\n{self.original_mask_token}\n}}"

    def sigonly(
        self, bug: RichBug
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Builds an instruction prompt for the given bug.

        Args:
            bug: The bug to generate the prompt for.
        Returns:
            Tuple: A tuple of the form (buggy_code, fixed_code, prompt).
        """
        result = extract_single_function(bug)
        if result is None:
            return None, None, None

        buggy_code, fixed_code = result

        # Get function signature of buggy code. Function can have @Annotations and such.
        # Keep everything except unnessessary whitespace and the body of the function.
        fixed_code_sig = buggy_code.split("{")[0].strip()
        prompt = self.function_body_infilling(fixed_code_sig)

        return buggy_code, fixed_code, prompt

    def prompt(self, bug: RichBug) -> dict[str, Optional[str]]:
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

        buggy_code, _ = extract_single_function(bug)
        if buggy_code is None:
            return result

        (
            result["buggy_code"],
            result["fixed_code"],
            result["prompt"],
        ) = self.sigonly(bug)
        return result