from elleelleaime.core.benchmarks.bug import Bug
from ..strategy import PromptingStrategy
from typing import Optional, Tuple
from unidiff import PatchSet
from uuid import uuid4
from elleelleaime.core.utils.java_tools.patch import read_patch
from elleelleaime.core.utils.java_tools.java_lang import (
    get_node_by_position,
    load_ast_nodes,
    load_origin_code_node,
)
import re, os, tempfile, shutil


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

        self.strict_one_hunk: bool = kwargs.get("strict_one_hunk", False)
        self.model_name: str = kwargs.get("model_name", "").strip().lower()
        assert (
            self.model_name in MASK_DICT.keys()
        ), f"Unknown model name: {kwargs.get('model_name', None)}"
        self.original_mask_token: str = MASK_DICT[self.model_name]
        self.pre_mask_token: str = None
        self.distance: int = None
        self.mask_token_id: int = kwargs.get("mask_token_id", 0)

    def single_diff_file_prompt(
        self,
        buggy_hunks: dict,
        fixed_hunks: dict,
        buggy_code_lines: list,
        fixed_code_lines: list,
    ) -> str:
        """Generate prompt by replacing all hunks with mask token."""
        if len(fixed_hunks) != 0:
            for value in fixed_hunks.values():
                self.distance, hunk = value
                fixed_code_lines = self.one_hunk_prompt(
                    [], hunk, "", fixed_code_lines
                ).split("\n")
            return "\n".join(fixed_code_lines)
        else:
            for value in buggy_hunks.values():
                self.distance, hunk = value
                buggy_code_lines = self.one_hunk_prompt(
                    hunk, [], buggy_code_lines, ""
                ).split("\n")
            return "\n".join(buggy_code_lines)

    def one_hunk_prompt(
        self,
        buggy_hunk: list,
        fixed_hunk: list,
        buggy_code_lines: list,
        fixed_code_lines: list,
    ) -> str:
        """Generate prompt by replacing one hunk with mask token."""
        prompt = []
        end_number = 0
        mask_token = (
            self.original_mask_token.format(self.mask_token_id)
            if "{}" in self.original_mask_token
            else self.original_mask_token
        )
        if not self.strict_one_hunk:
            if self.mask_token_id != 0:
                self.pre_mask_token = (
                    self.original_mask_token.format(self.mask_token_id - 1)
                    if "{}" in self.original_mask_token
                    else self.original_mask_token
                )
            self.mask_token_id += 1
        if len(fixed_hunk) != 0:
            for idx, line in enumerate(fixed_code_lines):
                # The length of fixed_hunk is 1
                if line.lstrip() == fixed_hunk[0].lstrip() and len(fixed_hunk) == 1:
                    if self.distance is None or self.distance == 0:
                        prompt.append(self.generate_masking_prompt(line, mask_token))
                    else:
                        located_index = idx - self.distance - 1
                        if (
                            fixed_code_lines[located_index].lstrip()
                            == self.pre_mask_token
                        ):
                            # print(fixed_code_lines[located_index].lstrip())
                            # print(self.pre_mask_token)
                            prompt.append(
                                self.generate_masking_prompt(line, mask_token)
                            )
                        else:
                            prompt.append(line)
                # The length of fixed_hunk is greater than 1, use the current line and the next line to assure the corret matching
                elif (
                    line.lstrip() == fixed_hunk[0].lstrip()
                    and fixed_code_lines[idx + 1].lstrip() == fixed_hunk[1].lstrip()
                ):
                    prompt.append(self.generate_masking_prompt(line, mask_token))
                    end_number = idx + len(fixed_hunk)
                # Skip the remaining lines in the fixed hunk
                elif idx < end_number:
                    continue
                else:
                    prompt.append(line)
            return "\n".join(prompt)
        else:
            for idx, line in enumerate(buggy_code_lines):
                # The length of buggy_hunk is 1
                if line.lstrip() == buggy_hunk[0] and len(buggy_hunk) == 1:
                    prompt.append(self.generate_masking_prompt(line, mask_token))
                    continue
                # The length of buggy_hunk is greater than 1, use the current line and the next line to assure the corret matching
                elif (
                    line.lstrip() == buggy_hunk[0]
                    and buggy_code_lines[idx + 1].lstrip() == buggy_hunk[1]
                ):
                    prompt.append(self.generate_masking_prompt(line, mask_token))
                    end_number = idx + len(buggy_hunk)
                # Skip the remaining lines in the buggy hunk
                elif idx < end_number:
                    continue
                else:
                    prompt.append(line)
            return "\n".join(prompt)

    def generate_masking_prompt(
        self, first_buggy_line: str, mask_token: str = None
    ) -> str:
        """Replace the first buggy line with mask token and keep the Java format."""

        # Find the leading spaces
        leading_spaces = re.match(r"^\s*", first_buggy_line).group()
        # Build the masking prompt
        return leading_spaces + mask_token

    def format_fixed_code_lines(
        self, fixed_code_lines: list, diff_lines: list, deleted_hunks: list
    ) -> list:
        """Insert hunk that only contains deleted lines into fixed code."""

        inserted_hunks = {}
        cnt = 0

        for deleted_hunk in deleted_hunks:
            located_lines = []
            for idx, line in enumerate(diff_lines):
                if deleted_hunk[0] == line:
                    # Use the before and after second liens to locate the hunk
                    located_lines.append(diff_lines[idx + len(deleted_hunk)])
                    located_lines.append(diff_lines[idx + len(deleted_hunk) + 1])
                    for idx, located_line in enumerate(located_lines):
                        if located_line.startswith("-") or located_line.startswith("+"):
                            located_lines[idx] = located_line[1:]
                    inserted_hunks[cnt] = (located_lines, deleted_hunk)
                    cnt += 1
                    continue

        for located_lines, deleted_hunk in inserted_hunks.values():
            for idx, line in enumerate(fixed_code_lines):
                if (
                    located_lines[0].lstrip() == fixed_code_lines[idx + 1].lstrip()
                    and located_lines[1].lstrip() == fixed_code_lines[idx + 2].lstrip()
                ):
                    # if located_lines[2].lstrip() == fixed_code_lines[idx + 2].lstrip() and located_lines[3].lstrip() == fixed_code_lines[idx + 3].lstrip():
                    leading_spaces = re.match(r"^\s*", line).group()
                    deleted_hunk = [
                        leading_spaces + line[1:].lstrip() for line in deleted_hunk
                    ]
                    fixed_code_lines = (
                        fixed_code_lines[: idx + 1]
                        + deleted_hunk
                        + fixed_code_lines[idx + 1 :]
                    )
                    break

        return fixed_code_lines

    def format_diff_lines(self, diff_lines: list) -> list:
        """
        Format the diff lines according to the following rules:
        - For continuous lines starting with '-' and '+', remove the '+'
        _ For continuous lines only starting with '-' or '+', keep it
        """

        formatted_lines = []
        temp_lines = []
        deleted_flag = False
        deleted_hunks = []

        for idx, line in enumerate(diff_lines):
            if line.startswith("-") and not line.startswith("--"):
                formatted_lines.append(line)
            elif (
                line.startswith("+") and not line.startswith("++") and not deleted_flag
            ):
                if not diff_lines[idx - 1].startswith("-") and not diff_lines[
                    idx - 1
                ].startswith("+"):
                    if not diff_lines[idx + 1].startswith("+") and not diff_lines[
                        idx + 1
                    ].startswith("-"):
                        formatted_lines.append(line)
                        deleted_hunks.append([line])
                    else:
                        deleted_flag = True
                        temp_lines.append(line)
            elif line.startswith("+") and not line.startswith("++") and deleted_flag:
                temp_lines.append(line)
                if not diff_lines[idx + 1].startswith("-") and not diff_lines[
                    idx + 1
                ].startswith("+"):
                    formatted_lines.extend(temp_lines)
                    deleted_hunks.append(temp_lines)
                    temp_lines = []
                    deleted_flag = False
                elif diff_lines[idx + 1].startswith("-"):
                    temp_lines = []
                    deleted_flag = False
            else:
                formatted_lines.append(line)

        for idx, line in enumerate(formatted_lines):
            if line.startswith("+") and not line.startswith("++"):
                formatted_lines[idx] = "-" + line[1:]

        for deleted_hunk in deleted_hunks:
            for idx, line in enumerate(deleted_hunk):
                if line.startswith("+") and not line.startswith("++"):
                    deleted_hunk[idx] = "-" + line[1:]

        return formatted_lines, deleted_hunks

    def find_all_diff_hunks(self, diff_lines: list, sign: str) -> list:
        """Find all the diff hunks in the diff text."""

        # inverse_sign = "-" if sign == "+" else "+"
        # diff_lines = [line for line in diff_lines if not line.startswith(inverse_sign)]
        diff_lines, deleted_hunks = self.format_diff_lines(diff_lines)

        # The value is the tuple of distance and hunk, and distance is the number of lines between two hunks
        # The distance of the first hunk is 0
        diff_hunks = {}
        distance = 0
        current_diff_hunk = []

        for line in diff_lines:
            if line.startswith(sign) and not line.startswith(sign * 2):
                current_diff_hunk.append(line[1:])
            else:
                if len(current_diff_hunk) != 0:
                    diff_hunks[len(diff_hunks)] = tuple([distance, current_diff_hunk])
                    current_diff_hunk = []
                    distance = 0
                if len(diff_hunks) != 0:
                    distance += 1
        return diff_hunks, diff_lines, deleted_hunks

    def find_longest_diff_hunk(self, diff_lines: list, sign: str) -> str:
        """Find the longest diff hunk in the diff text."""

        max_len = 0
        current_len = 0
        longest_diff_hunk = []
        current_diff_hunk = []

        for line in diff_lines:
            if line.startswith(sign) and not line.startswith(sign * 2):
                current_len += 1
                current_diff_hunk.append(line)
            else:
                if current_len > max_len:
                    max_len = current_len
                    longest_diff_hunk = current_diff_hunk
                current_len = 0
                current_diff_hunk = []

        return longest_diff_hunk

    def load_code_node(self, fixed_file_path, buggy_file_path, countable_diffs):
        fixed_node, i = load_origin_code_node(
            fixed_file_path, countable_diffs[0].sorted_changes()
        )
        try:
            buggy_nodes = load_ast_nodes(buggy_file_path)
            buggy_node = get_node_by_position(buggy_nodes, fixed_node, i)
        except Exception as e:
            print(e)
            return fixed_node, None
        return fixed_node, buggy_node

    def cloze_prompt(self, bug: Bug) -> Tuple[str, str, str]:
        """
        Building prompt by masking.

        Args:
            bug: The bug to generate the prompt for..
            mask_token (str): The mask token used to build the prompt.
            strict_one_hunk (bool): If true, use the longest diff hunk to pruduce cloze prompt. If two hunks have the same length, use the first one.
                                    If false, use all the individual hunks to produce cloze prompt.
        Returns:
            Tuple: A tuple of the form (buggy_code, fixed_code, prompt) or None if the prompt cannot be generated.
        """
        # breakpoint()
        diff_text = bug.get_ground_truth()
        countable_diffs = read_patch(diff_text)

        buggy_path = os.path.join(
            tempfile.gettempdir(), "elleelleaime", bug.get_identifier(), str(uuid4())
        )
        fixed_path = os.path.join(
            tempfile.gettempdir(), "elleelleaime", bug.get_identifier(), str(uuid4())
        )
        bug.checkout(buggy_path, fixed=False)
        bug.checkout(fixed_path, fixed=True)

        buggy_bug_path = os.path.join(buggy_path, countable_diffs[0].file_path)
        fixed_bug_path = os.path.join(fixed_path, countable_diffs[0].file_path)

        # Get the buggy and fixed code nodes
        fixed_node, buggy_node = self.load_code_node(
            fixed_bug_path, buggy_bug_path, countable_diffs
        )
        # Get the buggy and fixed code without comments
        fixed_code = fixed_node.code_lines_str(include_comment_line=False)
        buggy_code = (
            buggy_node.code_lines_str(include_comment_line=False)
            if buggy_node is not None
            else None
        )

        # Remove the checked-out bugs
        shutil.rmtree(buggy_path, ignore_errors=True)
        shutil.rmtree(fixed_path, ignore_errors=True)

        fixed_code_lines = fixed_code.split("\n")
        buggy_code_lines = buggy_code.split("\n") if buggy_code is not None else []

        # Remove the comment lines
        diff_lines = []
        for line in diff_text.split("\n"):
            if line.strip() == "":
                diff_lines.append(line)
            if re.sub("//.*", "", line).strip() != "":
                diff_lines.append(line)

        if self.strict_one_hunk:
            fixed_hunk = [
                code_line[1:]
                for code_line in self.find_longest_diff_hunk(diff_lines, "-")
            ]
            buggy_hunk = [
                code_line[1:]
                for code_line in self.find_longest_diff_hunk(diff_lines, "+")
            ]
            prompt = self.one_hunk_prompt(
                buggy_hunk, fixed_hunk, buggy_code_lines, fixed_code_lines
            )
        else:
            fixed_hunks, diff_lines, deleted_hunks = self.find_all_diff_hunks(
                diff_lines, "-"
            )
            # breakpoint()
            if len(deleted_hunks) > 0:
                fixed_code_lines = self.format_fixed_code_lines(
                    fixed_code_lines, diff_lines, deleted_hunks
                )
            buggy_hunks = self.find_all_diff_hunks(diff_lines, "+")
            prompt = self.single_diff_file_prompt(
                buggy_hunks, fixed_hunks, buggy_code_lines, fixed_code_lines
            )

        return buggy_code, fixed_code, prompt

    def prompt(self, bug: Bug) -> Optional[Tuple[str, str, str]]:
        """
        Returns the prompt for the given bug.

        :param bug: The bug to generate the prompt for.
        """

        diff = PatchSet(bug.get_ground_truth())
        # This strategy only supports single diff file bugs
        if len(diff) != 1 or len(diff[0]) != 1:
            return None

        buggy_code, fixed_code, prompt = self.cloze_prompt(bug)

        return buggy_code, fixed_code, prompt
