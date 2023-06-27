from core.benchmarks.bug import Bug
from sample.prompting.strategy import PromptingStrategy
from typing import Optional, Tuple
from unidiff import PatchSet

class ZeroShotSingleHunkPrompting(PromptingStrategy):
    """
    Implements the zero-shot single-hunk prompt strategy.
    """

    def __init__(self):
        super().__init__()
        self.template = """
        // Fix the following bug
        {buggy_code}
        // This is the fixed code
        """

    def prompt(self, bug: Bug, *args) -> Optional[Tuple[str, str, str]]:
        """
        Returns the prompt for the given bug.

        :param bug: The bug to generate the prompt for.
        :return: A tuple of the form (buggy_code, fixed_code, prompt) or None if the prompt cannot be generated.
        """
        diff = PatchSet(bug.get_ground_truth())
        # This strategy only supports single-hunk bugs
        if len(diff) != 1 or len(diff[0]) != 1:
            return None
        
        buggy_code = "".join([x.value for x in list(diff[0][0].target_lines())])
        fixed_code = "".join([x.value for x in list(diff[0][0].source_lines())])
        prompt = self.template.format(buggy_code=buggy_code)

        return buggy_code, fixed_code, prompt