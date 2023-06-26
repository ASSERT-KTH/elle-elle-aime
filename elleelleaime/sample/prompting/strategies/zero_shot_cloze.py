from core.benchmarks.bug import Bug
from core.utils.cloze_prompt import cloze_prompt
from ..strategy import PromptingStrategy
from typing import Optional, Tuple
from unidiff import PatchSet


class ZeroShotClozePrompting(PromptingStrategy):
    """
    Implements the zero-shot single-hunk prompt strategy for single diff file.
    """
    def __init__(self):
        super().__init__()

    def prompt(self, bug: Bug, mask_token: str, strict_one_hunk: bool) -> Optional[Tuple[str, str, str]]:
        """
        Returns the prompt for the given bug.

        :param bug: The bug to generate the prompt for.
        :param mask_token: The mask token used to build the prompt.
        :param strict_one_hunk: If true, use the longest diff hunk to pruduce cloze prompt. If two hunks have the same length, use the first one.
                                If false, use all the individual hunks in one diff file to produce cloze prompt.
        :return: A tuple of the form (buggy_code, fixed_code, prompt) or None if the prompt cannot be generated.
        """

        diff = PatchSet(bug.get_ground_truth())
        # This strategy only supports single diff file bugs
        if len(diff) != 1 or len(diff[0]) != 1:
            return None

        buggy_code,fixed_code, prompt = cloze_prompt(bug, mask_token, strict_one_hunk)

        return buggy_code, fixed_code, prompt