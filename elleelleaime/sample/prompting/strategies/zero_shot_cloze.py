from typing import Optional, Tuple, List
from unidiff import PatchSet
from uuid import uuid4
import re, os, tempfile, shutil, difflib

from ..strategy import PromptingStrategy
from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.utils.java_tools.java_lang import load_origin_code_node


MASK_DICT = {
    "incoder": "<|mask:{}|>",
    "plbart": "<mask>",
    "codet5": "<extra_id_{}>",
    # Add the model you want to use here
}


class ZeroShotClozePrompting(PromptingStrategy):
    """
    Implements the zero-shot cloze style prompt strategy for single diff file.
    """

    def __init__(self, **kwargs):
        super().__init__()

        self.model_name: str = kwargs.get("model_name", "").strip().lower()
        assert (
            self.model_name in MASK_DICT.keys()
        ), f"Unknown model name: {kwargs.get('model_name', None)}"
        self.original_mask_token: str = MASK_DICT[self.model_name]

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

    def find_code(self, file_path: str, line_numbers: List[int]) -> str:
        """
        Finds the code corresponding to the given line numbers in the given file.
        """
        code = ""
        with open(file_path, "r") as file:
            for idx, line in enumerate(file.readlines()):
                if idx + 1 in line_numbers:
                    code += line
        return code

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
        buggy_path = os.path.join(
            tempfile.gettempdir(), "elleelleaime", bug.get_identifier(), str(uuid4())
        )
        fixed_path = os.path.join(
            tempfile.gettempdir(), "elleelleaime", bug.get_identifier(), str(uuid4())
        )

        try:
            # Note: this diff is inverted, i.e. the target file is the buggy file
            diff = PatchSet(bug.get_ground_truth())

            bug.checkout(buggy_path, fixed=False)
            bug.checkout(fixed_path, fixed=True)

            buggy_file_path = os.path.join(
                buggy_path, diff[0].target_file.replace("b/", "", 1)
            )
            fixed_file_path = os.path.join(
                fixed_path, diff[0].source_file.replace("a/", "", 1)
            )

            # Find the methods of each hunk
            buggy_methods = []
            fixed_methods = []
            allowed_node_types = ["MethodDeclaration", "ConstructorDeclaration"]
            for hunk in diff[0]:
                buggy_methods.append(
                    load_origin_code_node(
                        buggy_file_path,
                        [x.target_line_no for x in hunk.target_lines()],
                        allowed_node_types,
                    )[0]
                )
                fixed_methods.append(
                    load_origin_code_node(
                        fixed_file_path,
                        [x.source_line_no for x in hunk.source_lines()],
                        allowed_node_types,
                    )[0]
                )

            # Verify that all hunk make changes in the same method
            buggy_method = buggy_methods[0]
            fixed_method = fixed_methods[0]
            for buggy_method, fixed_method in zip(buggy_methods, fixed_methods):
                if buggy_method != buggy_methods[0] or fixed_method != fixed_methods[0]:
                    return None, None, None

            # Get the buggy and fixed code with line numbers
            # If the ast nodes are not of the correct type, then we have a whole-function removal/addition
            buggy_code = (
                self.find_code(
                    buggy_file_path,
                    [
                        i
                        for i in range(buggy_method.start_pos, buggy_method.end_pos + 1)
                    ],
                )
                if buggy_method is not None
                else ""
            )
            fixed_code = (
                self.find_code(
                    fixed_file_path,
                    [
                        i
                        for i in range(fixed_method.start_pos, fixed_method.end_pos + 1)
                    ],
                )
                if fixed_method is not None
                else ""
            )

            # Compute the function diff
            def compute_function_diff(buggy_code: str, fixed_code: str) -> List[str]:
                return list(
                    difflib.unified_diff(
                        buggy_code.splitlines(keepends=True),
                        fixed_code.splitlines(keepends=True),
                        n=max(len(buggy_code), len(fixed_code)),
                    )
                )

            # Check if the computed diff is equivalent to the original diff
            def assert_same_diff(
                original_diff: PatchSet, function_diff: List[str]
            ) -> bool:
                original_changed_lines = []
                for file in original_diff:
                    for hunk in file:
                        for line in hunk:
                            if not line.is_context:
                                original_changed_lines.append(line.value)
                for line in function_diff:
                    if any(line.startswith(x) for x in ["---", "+++", "@@"]):
                        continue
                    if any(line.startswith(x) for x in ["+", "-"]):
                        if (
                            line[1:] not in original_changed_lines
                            and line[1:].strip() != ""
                        ):
                            return False
                        elif line[1:].strip() != "":
                            original_changed_lines.remove(line[1:])
                if len(original_changed_lines) > 0:
                    for line in original_changed_lines:
                        return False
                return True

            # HACK: sometimes we are not able to properly retrieve the code at the function-level
            # This happens in cases suchas Closure-46 where a whole function is removed
            # To detected and circumvent such cases, we check that the function_diff is equivalent to the original diff
            # If the diffs are not equivalent, we try to fix the function diff by setting the fixed_code and buggy_code to empty
            # If on of these works we assume it as correct (since the diff is now equivalent to the original one)
            fdiff = compute_function_diff(buggy_code, fixed_code)
            if not assert_same_diff(diff, fdiff):
                fdiff = compute_function_diff(buggy_code, "")
                if assert_same_diff(diff, fdiff):
                    fixed_code = ""
                else:
                    fdiff = compute_function_diff("", fixed_code)
                    if assert_same_diff(diff, fdiff):
                        buggy_code = ""
                    else:
                        return None, None, None

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
                    prompt += f"{self.generate_masking_prompt(fdiff[i][1:], mask_id)}\n"
                    mask_id += 1
                    # Skip over the remainder of the added/removed chunk
                    while i < len(fdiff) and any(
                        fdiff[i].startswith(x) for x in ["+", "-"]
                    ):
                        i += 1
                # Include unchanged lines
                else:
                    prompt += fdiff[i][1:]
                    i += 1

            # Deal with whole-function addition/removal
            if prompt == "":
                prompt = f"{self.generate_masking_prompt('', 0)}"

            return buggy_code, fixed_code, prompt

        finally:
            # Remove the checked-out bugs
            shutil.rmtree(buggy_path, ignore_errors=True)
            shutil.rmtree(fixed_path, ignore_errors=True)

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
