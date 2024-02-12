from typing import Optional, Tuple, Union, List

from elleelleaime.sample.mufin.strategy import MufinStrategy
from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.utils.java_tools.java import (
    extract_functions,
    remove_java_comments,
    remove_empty_lines,
)

import hashlib


class BreakerStrategy(MufinStrategy):
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

    def __init__(self, **kwargs):
        super().__init__("mufin-breaker")

        self.model_name: str = kwargs.get("model_name", "").strip().lower()
        assert (
            self.model_name in self.MODEL_DICT.keys()
        ), f"Unknown model name: {kwargs.get('model_name', None)}"
        model_kwargs = self.MODEL_DICT.get(self.model_name, {})
        self.prefix_token: str = model_kwargs["prefix_token"]
        self.middle_token: str = model_kwargs["middle_token"]
        self.sufix_token: str = model_kwargs["sufix_token"]
        self.keep_buggy_code: bool = kwargs.get("keep_buggy_code", False)
        self.keep_comments: bool = kwargs.get("keep_comments", False)

    def build_fim_prompt(self, code: str, start_line: int, end_line: int) -> str:
        split_code = code.splitlines(keepends=True)
        prefix: str = "".join(split_code[:start_line])
        middle: str = "".join(split_code[start_line:end_line])
        suffix: str = "".join(split_code[end_line:])

        if self.keep_buggy_code:
            buggy_comment = "// buggy code\n"
            if middle.strip() != "":
                for line in middle.splitlines(keepends=True):
                    buggy_comment += "//" + line
            prompt = (
                f"{self.prefix_token}"
                + prefix
                + buggy_comment
                + f"{self.sufix_token}"
                + suffix
                + f"{self.middle_token}"
            )
        else:
            prompt = (
                f"{self.prefix_token}"
                + prefix
                + f"{self.sufix_token}"
                + suffix
                + f"{self.middle_token}"
            )

        return prompt

    def enumerate_spans(self, function_code: str) -> List[Tuple[int, int]]:
        """
        Enumerates the spans inside a function. Does not include function signature and closing brackets.
        """
        result = []
        lines = function_code.splitlines()
        for i, _ in enumerate(lines):
            # Skip the function signature and closing brackets
            if i == 0 or i == len(lines) - 1:
                continue
            for j, _ in enumerate(lines[i:-1]):
                result.append((i, i + j))
        return result

    def expand_spans(
        self, bug: Bug, function: dict[str, str], spans: List[Tuple[int, int]]
    ) -> List[dict[str, Optional[str]]]:
        """
        Expands the spans into prompts.
        """
        result = []
        for span in spans:
            prompt = self.build_fim_prompt(
                function["clean_function_code"], span[0], span[1]
            )
            result.append(
                {
                    "identifier": bug.get_identifier(),
                    "buggy_code": None,
                    "fixed_code": function["function_code"],
                    "prompt_strategy": self.strategy_name,
                    "prompt": prompt,
                    "file_path": str(function["file_path"]),
                }
            )
        return result

    def sample(self, bug: Bug) -> List[dict[str, Optional[Union[str, Tuple]]]]:
        """
        Returns the prompt for the given bug.

        :param bug: The bug to generate the prompt for.
        """
        result = []

        # Extract functions from the *.java files in the checkout directory
        functions = extract_functions(bug, fixed=True)

        # Sanitize the functions
        for function in functions:
            code = function["function_code"]
            if not self.keep_comments:
                code = remove_java_comments(code)
            code = remove_empty_lines(code)
            code = code.strip()
            function["clean_function_code"] = code

        # Enumerate the spans inside each function
        # Build a prompt for each of the spans
        for function in functions:
            spans = self.enumerate_spans(function["clean_function_code"])
            # Expand the spans into prompts
            prompts = self.expand_spans(bug, function, spans)

            # Generate hash based on prompt and identifier
            for p in prompts:
                p["hash"] = hashlib.md5(
                    f"{p['prompt']}-{p['identifier']}".encode("utf-8")
                ).hexdigest()

            result.extend(prompts)

        return result
