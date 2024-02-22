from typing import Optional, Tuple, List, Union
from unidiff import PatchSet
import hashlib

from elleelleaime.sample.mufin.strategy import MufinStrategy
from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.utils.java_tools.java import (
    extract_single_function,
    compute_diff,
    remove_java_comments,
    remove_empty_lines,
)


class EvalStrategy(MufinStrategy):
    # MODEL_DICT is a dictionary of model names and their corresponding kwargs
    MODEL_DICT = {
        "starcoder": {
            "prefix_token": "<fim_prefix>",
            "middle_token": "<fim_middle>",
            "sufix_token": "<fim_suffix>",
        },
        # Add the model you want to use here
    }

    MODE_TOKEN = {
        "fixer": "<FIXER>",
        "breaker": "<BREAKER>",
    }

    def __init__(self, **kwargs):
        super().__init__("mufin-eval")

        self.model_name: str = kwargs.get("model_name", "starcoder").strip().lower()
        assert (
            self.model_name in self.MODEL_DICT.keys()
        ), f"Unknown model name: {kwargs.get('model_name', None)}"
        model_kwargs = self.MODEL_DICT.get(self.model_name, {})
        self.prefix_token: str = model_kwargs["prefix_token"]
        self.middle_token: str = model_kwargs["middle_token"]
        self.sufix_token: str = model_kwargs["sufix_token"]
        self.keep_buggy_code: bool = kwargs.get("keep_buggy_code", True)
        self.keep_comments: bool = kwargs.get("keep_comments", False)
        self.mode: str = kwargs.get("mode", "fixer")
        assert self.mode in self.MODE_TOKEN.keys(), f"Unknown mode: {self.mode}"
        self.mode_token: str = self.MODE_TOKEN[self.mode]

    def build_fim_prompt(self, buggy_code: str, fixed_code: str) -> str:
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
                if line.startswith("-"):
                    middle += line[1:]
            else:
                if prefix[0]:
                    prefix[1] += line[1:]
                elif suffix[0]:
                    suffix[1] += line[1:]

        if self.keep_buggy_code:
            buggy_comment = "// buggy code\n"
            if middle.strip() != "":
                for line in middle.splitlines(keepends=True):
                    buggy_comment += "//" + line
            prompt = (
                f"{self.mode_token}"
                + f"{self.prefix_token}"
                + prefix[1]
                + buggy_comment
                + f"{self.sufix_token}"
                + suffix[1]
                + f"{self.middle_token}"
            )
        else:
            prompt = (
                f"{self.mode_token}"
                + f"{self.prefix_token}"
                + prefix[1]
                + f"{self.sufix_token}"
                + suffix[1]
                + f"{self.middle_token}"
            )

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

        if not self.keep_comments:
            buggy_code_prompt = remove_java_comments(buggy_code)
            fixed_code_prompt = remove_java_comments(fixed_code)
        else:
            buggy_code_prompt = buggy_code
            fixed_code_prompt = fixed_code

        buggy_code_prompt = remove_empty_lines(buggy_code_prompt)
        fixed_code_prompt = remove_empty_lines(fixed_code_prompt)

        prompt = self.build_fim_prompt(buggy_code_prompt, fixed_code_prompt)

        return buggy_code, fixed_code, prompt

    def sample(self, bug: Bug) -> List[dict[str, Optional[Union[str, Tuple]]]]:
        """
        Returns the prompt for the given bug.

        :param bug: The bug to generate the prompt for.
        """
        result = {
            "hash": hashlib.md5(bug.get_identifier().encode("utf-8")).hexdigest(),
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
            return [result]

        (
            result["buggy_code"],
            result["fixed_code"],
            result["prompt"],
        ) = self.cloze_prompt(bug)
        return [result]
