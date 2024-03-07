from typing import Optional, List, Union, Tuple
from unidiff import PatchSet

from elleelleaime.process.mufin.strategy import MufinProcessStrategy
from elleelleaime.core.utils.java_tools.java import (
    compute_diff,
    remove_java_comments,
    remove_empty_lines,
)


class MufinV1Strategy(MufinProcessStrategy):
    """
    Implements the breaker sampling strategy for single diff file.
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

    FIXER_TOKEN = "<FIXER>"
    BREAKER_TOKEN = "<BREAKER>"

    def __init__(self, **kwargs):
        super().__init__("mufinv1")
        self.model_name: str = kwargs.get("model_name", "").strip().lower()
        assert (
            self.model_name in self.MODEL_DICT.keys()
        ), f"Unknown model name: {kwargs.get('model_name', None)}"
        model_kwargs = self.MODEL_DICT.get(self.model_name, {})
        self.prefix_token: str = model_kwargs["prefix_token"]
        self.middle_token: str = model_kwargs["middle_token"]
        self.sufix_token: str = model_kwargs["sufix_token"]
        self.keep_buggy_code: bool = kwargs.get("keep_buggy_code", True)
        self.keep_comments: bool = kwargs.get("keep_comments", False)
        self.critic: str = kwargs.get("critic", "keepall")
        assert self.critic in [
            "keepall",
            "compiler",
            "test",
        ], f"Unknown critic: {self.critic}"

    def build_fim_prompt(
        self, source_code: str, target_code: str, mode_token: str
    ) -> Tuple[str, str]:
        # Clean the source and target code
        source_code = source_code.strip()
        target_code = target_code.strip()
        if not self.keep_comments:
            source_code = remove_java_comments(source_code)
            target_code = remove_java_comments(target_code)
        source_code = remove_empty_lines(source_code)
        target_code = remove_empty_lines(target_code)

        # Compute the diff
        fdiff = compute_diff(source_code, target_code)

        # Iterate over the diff to get the prefix, middle, and suffix parts
        prefix = [True, ""]
        middle = ""
        target = ""
        suffix = [False, ""]
        for line in fdiff:
            if any(line.startswith(x) for x in ["---", "+++", "@@"]):
                continue
            elif any(line.startswith(x) for x in ["+", "-"]):
                prefix[0] = False
                suffix[0] = True
                middle += suffix[1]
                target += suffix[1]
                suffix[1] = ""
                if line.startswith("-"):
                    middle += line[1:]
                elif line.startswith("+"):
                    target += line[1:]
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
                f"{mode_token}\n"
                + f"{self.prefix_token}"
                + prefix[1]
                + buggy_comment
                + f"{self.sufix_token}"
                + suffix[1]
                + f"{self.middle_token}"
            )
        else:
            prompt = (
                f"{mode_token}\n"
                + f"{self.prefix_token}"
                + prefix[1]
                + f"{self.sufix_token}"
                + suffix[1]
                + f"{self.middle_token}"
            )

        return prompt, target

    def breaker_prompt(
        self,
        bug: dict[str, Union[List[str], Optional[str]]],
    ) -> Tuple[Optional[str], Optional[str]]:
        diff = PatchSet(bug["diff"])
        fixed_code = "".join(line.value for line in diff[0][0] if not line.is_added)
        buggy_code = "".join(line.value for line in diff[0][0] if not line.is_removed)
        return self.build_fim_prompt(
            fixed_code, buggy_code, mode_token=self.BREAKER_TOKEN
        )

    def fixer_prompt(
        self,
        bug: dict[str, Union[List[str], Optional[str]]],
    ) -> Tuple[Optional[str], Optional[str]]:
        diff = PatchSet(bug["diff"])
        fixed_code = "".join(line.value for line in diff[0][0] if not line.is_added)
        buggy_code = "".join(line.value for line in diff[0][0] if not line.is_removed)
        return self.build_fim_prompt(
            buggy_code, fixed_code, mode_token=self.FIXER_TOKEN
        )

    def process(
        self, bug: dict[str, Union[List[str], Optional[str]]]
    ) -> List[dict[str, Optional[str]]]:
        """
        Processes the bug and returns a list of samples.
        """
        results = []
        prompt, target = self.breaker_prompt(bug)
        if prompt and target:
            results.append(
                {
                    "prompt": prompt,
                    "target": target,
                }
            )
        prompt, target = self.fixer_prompt(bug)
        if prompt and target:
            results.append(
                {
                    "prompt": prompt,
                    "target": target,
                }
            )
        return results
