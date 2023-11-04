from typing import Optional, Tuple, List
from unidiff import PatchSet
import re

from elleelleaime.sample.prompting.strategy import PromptingStrategy
from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.utils.java_tools.java import (
    extract_single_function,
    compute_diff,
)


class ZeroShotClozePrompting(PromptingStrategy):
    """
    Implements the zero-shot cloze style prompt strategy for single diff file.
    """

    # MODEL_DICT is a dictionary of model names and their corresponding kwargs
    MODEL_DICT = {
        "incoder": {
            "mask_token": "<|mask:{}|>",
            "extra_mask_token": True,
            "single_chunk": False,
        },
        "codellama": {
            "mask_token": "<FILL_ME>",
            "extra_mask_token": False,
            "single_chunk": True,
        },
        # Add the model you want to use here
    }

    def __init__(self, **kwargs):
        super().__init__()

        self.model_name: str = kwargs.get("model_name", "").strip().lower()
        assert (
            self.model_name in self.MODEL_DICT.keys()
        ), f"Unknown model name: {kwargs.get('model_name', None)}"
        model_kwargs = self.MODEL_DICT.get(self.model_name, {})
        self.original_mask_token: str = model_kwargs["mask_token"]
        self.extra_mask_token: bool = model_kwargs.get("extra_mask_token", False)
        self.keep_buggy_code: bool = kwargs.get("keep_buggy_code", False)

    def generate_masking_prompt(self, line_to_replace: str, mask_id: int) -> str:
        """Generate the mask token to be inserted, according to the mask idx."""
        # Generate the mask token
        mask_token = (
            self.original_mask_token.format(mask_id)
            if "{}" in self.original_mask_token
            else self.original_mask_token
        )

        # Find the leading spaces
        leading_spaces = re.match(r"^\s*", line_to_replace)
        if leading_spaces is not None:
            leading_spaces = leading_spaces.group()
        else:
            leading_spaces = ""

        # Build the masking prompt
        return leading_spaces + mask_token

    def build_multi_cloze_prompt(self, buggy_code: str, fixed_code: str) -> str:
        fdiff = compute_diff(buggy_code, fixed_code)

        # Iterate over both the buggy and fixed code to generate the prompt
        prompt = ""
        mask_id = 0
        i = 0
        while i < len(fdiff):
            # Ignore garbage
            if any(fdiff[i].startswith(x) for x in ["---", "+++", "@@"]):
                i += 1
            # Add a mask token in added/removed chunk of code
            elif any(fdiff[i].startswith(x) for x in ["+", "-"]):
                # If we keep the buggy code we add a first line signaling it and then the first buggy line
                if self.keep_buggy_code and fdiff[i].startswith("-"):
                    prompt += "// buggy code\n//" + fdiff[i][1:]
                # We generate the mask token with the leading spaces of the first buggy line
                mask_token = self.generate_masking_prompt(fdiff[i][1:], mask_id)
                i += 1
                # Skip over the remainder of the added/removed chunk
                while i < len(fdiff) and any(
                    fdiff[i].startswith(x) for x in ["+", "-"]
                ):
                    # Keep buggy lines if the option is true
                    if self.keep_buggy_code and fdiff[i].startswith("-"):
                        prompt += "//" + fdiff[i][1:]
                    i += 1
                # Add the mask token after all buggy lines have been processed
                prompt += f"{mask_token}\n"
                mask_id += 1
            # Include unchanged lines
            else:
                prompt += fdiff[i][1:]
                i += 1

        # Add extra mask token (e.g. Incoder recommends this in Section 2.2 of their paper)
        if self.extra_mask_token:
            prompt += f"{self.generate_masking_prompt('', mask_id)}\n"

        # Deal with whole-function addition/removal
        if prompt == "":
            prompt = f"{self.generate_masking_prompt('', 0)}"

        return prompt

    def build_single_cloze_prompt(self, buggy_code: str, fixed_code: str) -> str:
        fdiff = compute_diff(buggy_code, fixed_code)

        # Iterate over the diff to get the prefix, middle, and suffix parts
        prefix = [True, ""]
        middle = ""
        suffix = [False, ""]
        for line in fdiff:
            if any(line.startswith(x) for x in ["---", "+++", "@@"]):
                continue
            elif any(line.startswith(x) for x in ["+", "-"]):
                prefix[0] = False
                suffix[0] = True
                middle += suffix[1]
                suffix[1] = ""
                middle += line[1:]
            else:
                if prefix[0]:
                    prefix[1] += line[1:]
                elif suffix[0]:
                    suffix[1] += line[1:]

        if self.keep_buggy_code:
            middle = "// buggy code\n" + "//".join(
                [line for line in buggy_code.splitlines(keepends=True)]
            )
            prompt = prefix[1] + middle + "<FILL_ME>\n" + suffix[1]
        else:
            prompt = prefix[1] + "<FILL_ME>\n" + suffix[1]

        return prompt

    def cloze_prompt(
        self, bug: Bug
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Builds a cloze prompt for the given bug.

        Args:
            bug: The bug to generate the prompt for.
        Returns:
            Tuple: A tuple of the form (buggy_code, fixed_code, prompt).
        """
        result = extract_single_function(bug)

        if result is None:
            return None, None, None

        buggy_code, fixed_code = result
        if self.MODEL_DICT[self.model_name]["single_chunk"]:
            prompt = self.build_single_cloze_prompt(buggy_code, fixed_code)
        else:
            prompt = self.build_multi_cloze_prompt(buggy_code, fixed_code)

        return buggy_code, fixed_code, prompt

    def prompt(self, bug: Bug) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Returns the prompt for the given bug.

        :param bug: The bug to generate the prompt for.
        """

        diff = PatchSet(bug.get_ground_truth())
        # This strategy only supports single-file prompts
        if len(diff) != 1:
            return None, None, None

        buggy_code, fixed_code, prompt = self.cloze_prompt(bug)

        return buggy_code, fixed_code, prompt
