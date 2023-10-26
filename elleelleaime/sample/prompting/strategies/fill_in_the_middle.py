from typing import Optional, Tuple, List
from unidiff import PatchSet

from elleelleaime.sample.prompting.strategy import PromptingStrategy
from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.utils.java_tools.java import (
    extract_single_function,
    compute_diff,
)


class FillInTheMiddlePrompting(PromptingStrategy):
    """
    Implements the fill-in-the-middle style prompt strategy for single diff file.
    """

    # MODEL_DICT is a dictionary of model names and their corresponding kwargs
    MODEL_DICT = {
        "starcoder": {
            "prefix_token": "<fim_prefix>",
            "middle_token": "<fim_middle>",
            "sufix_token": "<fim_suffix>",
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
        self.prefix_token: str = model_kwargs["prefix_token"]
        self.middle_token: str = model_kwargs["middle_token"]
        self.sufix_token: str = model_kwargs["sufix_token"]

    def find_code(self, file_path: str, line_numbers: List[int]) -> str:
        """
        Finds the code corresponding to the given line numbers in the given file.
        """
        code = ""
        with open(file_path, "r", encoding="ISO-8859-1") as file:
            for idx, line in enumerate(file.readlines()):
                if idx + 1 in line_numbers:
                    code += line
        return code

    def is_single_chunk(self, diff_str: str) -> bool:
        """
        Return True if the sample's ground truth is a single chunk.
        Single chunk means that there is only one hunk in the ground truth and that the changes are all contiguous.
        """
        diff = PatchSet(diff_str)
        # Check if there is only one hunk
        if len(diff) == 1 and len(diff[0]) == 1:
            # Check if the changes are contiguous
            hunk = diff[0][0]
            i = 0
            found_change = False
            while i < len(hunk):
                # Find a change
                if hunk[i].is_added or hunk[i].is_removed:
                    if found_change:
                        return False
                    found_change = True
                    # Skip over the remainder of the added/removed chunk
                    while i < len(hunk) and (hunk[i].is_added or hunk[i].is_removed):
                        i += 1
                # Skip over the unchanged chunk
                else:
                    i += 1
            return True
        else:
            return False

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
        if not self.is_single_chunk(bug.get_ground_truth()):
            return None, None, None

        result = extract_single_function(bug)

        if result is None:
            return None, None, None

        fdiff = compute_diff(*result)

        # Iterate over both the buggy and fixed code to generate the prompt
        prompt = f"{self.prefix_token}"
        i = 0
        while i < len(fdiff):
            # Ignore garbage
            if any(fdiff[i].startswith(x) for x in ["---", "+++", "@@"]):
                i += 1
            # Skip over the chunk
            elif any(fdiff[i].startswith(x) for x in ["+", "-"]):
                # Skip over the remainder of the added/removed chunk
                while i < len(fdiff) and any(
                    fdiff[i].startswith(x) for x in ["+", "-"]
                ):
                    i += 1
                prompt += f"{self.sufix_token}"
            # Include unchanged lines
            else:
                prompt += fdiff[i][1:]
                i += 1

        # Deal with whole function removal/addition
        if not self.sufix_token in prompt:
            prompt += f"{self.sufix_token}"

        prompt += f"{self.middle_token}"

        return result[0], result[1], prompt

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
