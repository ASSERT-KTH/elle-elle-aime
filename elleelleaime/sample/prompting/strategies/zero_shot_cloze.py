from core.benchmarks.bug import Bug
from ..strategy import PromptingStrategy
from typing import Optional, Tuple
from unidiff import PatchSet
from uuid import uuid4
from core.utils.java_tools.patch import read_patch
from core.utils.java_tools.java_lang import get_node_by_position, load_ast_nodes, load_origin_code_node
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
    def __init__(self):
        super().__init__()

    def sinfle_diff_file_prompt(self, buggy_hunks: list, fixed_hunks: list, buggy_code_lines: list, fixed_code_lines: list, mask_token: str=None) -> str:
        """Generate prompt by replacing all hunks with mask token."""
        if len(fixed_hunks) != 0:
            for hunk in fixed_hunks:
                fixed_code_lines = self.one_hunk_prompt([], hunk, '', fixed_code_lines, mask_token).split('\n')
            return '\n'.join(fixed_code_lines)
        else:
            for hunk in buggy_hunks:
                buggy_code_lines = self.one_hunk_prompt(hunk, [], buggy_code_lines, '', mask_token).split('\n')
            return '\n'.join(buggy_code_lines)

    def one_hunk_prompt(self, buggy_hunk: list, fixed_hunk: list, buggy_code_lines: list, fixed_code_lines: list, mask_token: str=None) -> str:
        """Generate prompt by replacing one hunk with mask token."""
        prompt = []
        end_number = 0
        if len(fixed_hunk) != 0:
            for idx, line in enumerate(fixed_code_lines):
                # The length of fixed_hunk is 1
                if line.lstrip() == fixed_hunk[0].lstrip() and len(fixed_hunk) == 1:
                    prompt.append(self.generate_masking_prompt(line, mask_token))
                    continue
                # The length of fixed_hunk is greater than 1, use the current line and the next line to assure the corret matching
                elif line.lstrip() == fixed_hunk[0].lstrip() and fixed_code_lines[idx+1].lstrip() == fixed_hunk[1].lstrip():
                    prompt.append(self.generate_masking_prompt(line, mask_token))
                    end_number = idx + len(fixed_hunk)
                # Skip the remaining lines in the fixed hunk
                elif idx < end_number:
                    continue
                else:
                    prompt.append(line)
            return '\n'.join(prompt) 
        else:
            for idx, line in enumerate(buggy_code_lines):
                # The length of buggy_hunk is 1
                if line.lstrip() == buggy_hunk[0] and len(buggy_hunk) == 1:
                    prompt.append(self.generate_masking_prompt(line, mask_token))
                    continue
                # The length of buggy_hunk is greater than 1, use the current line and the next line to assure the corret matching
                elif line.lstrip() == buggy_hunk[0] and buggy_code_lines[idx+1].lstrip() == buggy_hunk[1]:
                    prompt.append(self.generate_masking_prompt(line, mask_token))
                    end_number = idx + len(buggy_hunk)
                # Skip the remaining lines in the buggy hunk
                elif idx < end_number:
                    continue
                else:
                    prompt.append(line)
            return '\n'.join(prompt) 
        
    def generate_masking_prompt(self, first_buggy_line: str, mask_token: str=None) -> str:
        """Replace the first buggy line with mask token and keep the Java format."""

        # Find the leading spaces
        leading_spaces = re.match(r'^\s*', first_buggy_line).group()
        # Build the masking prompt
        return leading_spaces + mask_token
    
    def load_code_node(self, fixed_file_path, buggy_file_path, countable_diffs):
        fixed_node, i = load_origin_code_node(
            fixed_file_path, countable_diffs[0].sorted_changes())
        buggy_nodes = load_ast_nodes(buggy_file_path)
        buggy_node = get_node_by_position(buggy_nodes, fixed_node, i)
        return fixed_node, buggy_node
    
    def find_all_diff_hunks(self, diff_text: str, sign: str) -> list:
        """Find all the diff hunks in the diff text."""

        lines = diff_text.split('\n')

        diff_hunks = []
        current_diff_hunk = []

        for line in lines:
            if line.startswith(sign) and not line.startswith(sign * 2):
                current_diff_hunk.append(line[1:])
            else:
                if len(current_diff_hunk) != 0:
                    diff_hunks.append(current_diff_hunk)
                current_diff_hunk = []
        
        return diff_hunks
    
    def find_longest_diff_hunk(self, diff_text: str, sign: str) -> str:
        """Find the longest diff hunk in the diff text."""

        lines = diff_text.split('\n')

        max_len = 0
        current_len = 0
        longest_diff_hunk = []
        current_diff_hunk = []

        for line in lines:
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
    
    def cloze_prompt(self, bug: Bug, mask_token: str, strict_one_hunk: bool) -> Optional[Tuple[str, str, str]]:
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

        buggy_path = os.path.join(tempfile.gettempdir(), "elleelleaime", bug.get_identifier(), uuid4())
        fixed_path = os.path.join(tempfile.gettempdir(), "elleelleaime", bug.get_identifier(), uuid4())
        bug.checkout(buggy_path, fixed=False)
        bug.checkout(fixed_path, fixed=True)

        buggy_bug_path = os.path.join(buggy_path, countable_diffs[0].file_path)
        fixed_bug_path = os.path.join(fixed_path, countable_diffs[0].file_path)

        # Get the buggy and fixed code nodes
        fixed_node, buggy_node = self.load_code_node(fixed_bug_path, buggy_bug_path, countable_diffs)
        # Get the buggy and fixed code without comments
        buggy_code, fixed_code = buggy_node.code_lines_str(include_comment_line=False), fixed_node.code_lines_str(include_comment_line=False)

        # Remove the checked-out bugs
        shutil.rmtree(buggy_path, ignore_errors=True)
        shutil.rmtree(fixed_path, ignore_errors=True)

        buggy_code_lines = buggy_code.split('\n')
        fixed_code_lines = fixed_code.split('\n')

        if strict_one_hunk:
            buggy_hunk = [code_line[1:] for code_line in self.find_longest_diff_hunk(diff_text, '+')]
            fixed_hunk = [code_line[1:] for code_line in self.find_longest_diff_hunk(diff_text, '-')]
            prompt = self.one_hunk_prompt(buggy_hunk, fixed_hunk, buggy_code_lines, fixed_code_lines, mask_token)
        else:
            buggy_hunks = self.find_all_diff_hunks(diff_text, '+')
            fixed_hunks = self.find_all_diff_hunks(diff_text, '-')
            prompt = self.sinfle_diff_file_prompt(buggy_hunks, fixed_hunks, buggy_code_lines, fixed_code_lines, mask_token)

        return buggy_code, fixed_code, prompt

    def prompt(self, bug: Bug, *args) -> Optional[Tuple[str, str, str]]:
        """
        Returns the prompt for the given bug.

        :param bug: The bug to generate the prompt for.
        :param mask_token: The mask token used to build the prompt.
        :param strict_one_hunk: If true, use the longest diff hunk to pruduce cloze prompt. If two hunks have the same length, use the first one.
                                If false, use all the individual hunks in one diff file to produce cloze prompt.
        :return: A tuple of the form (buggy_code, fixed_code, prompt) or None if the prompt cannot be generated.
        """

        model_name, strict_one_hunk = args[:2]
        assert model_name in MASK_DICT.keys(), f"Unknown model name: {model_name}"

        mask_token = MASK_DICT[model_name.lower()]

        diff = PatchSet(bug.get_ground_truth())
        # This strategy only supports single diff file bugs
        if len(diff) != 1 or len(diff[0]) != 1:
            return None

        buggy_code,fixed_code, prompt = self.cloze_prompt(bug, mask_token, strict_one_hunk)

        return buggy_code, fixed_code, prompt