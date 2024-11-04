from typing import Optional, Tuple
from unidiff import PatchSet

from elleelleaime.sample.strategy import PromptingStrategy
from elleelleaime.core.benchmarks.bug import RichBug
from elleelleaime.core.utils.java.java import (
    extract_single_function,
    extract_failing_test_cases,
)


class SigOnlyInstructPrompting(PromptingStrategy):
    """
    Implements function signature instruction prompting strategies.
    """

    def __init__(self, **kwargs):
        super().__init__("sigonly-instruct")

    def sigonly_instruct(
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

        prompt = f"""Please complete the following function:

```java
{fixed_code_sig}
```

Provide the completed function inside a code block."""

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

        (
            result["buggy_code"],
            result["fixed_code"],
            result["prompt"],
        ) = self.sigonly_instruct(bug)
        return result
