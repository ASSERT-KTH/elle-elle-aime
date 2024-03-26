from typing import Optional, Tuple, List
from unidiff import PatchSet
from pathlib import Path
from uuid import uuid4
import os, tempfile, difflib, shutil
import re

from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.utils.java_tools.java_lang import load_origin_code_node


def find_code(file_path: str, line_numbers: List[int]) -> str:
    """
    Finds the code corresponding to the given line numbers in the given file.
    """
    code = ""
    with open(file_path, "r", encoding="ISO-8859-1") as file:
        for idx, line in enumerate(file.readlines()):
            if idx + 1 in line_numbers:
                code += line
    return code


def compute_diff(
    buggy_code: str, fixed_code: str, context_len: Optional[int] = None
) -> List[str]:
    """
    Computes the diff between the buggy and fixed code.
    """
    context_len = (
        context_len
        if context_len is not None
        else max(len(buggy_code), len(fixed_code))
    )
    return list(
        difflib.unified_diff(
            buggy_code.splitlines(keepends=True),
            fixed_code.splitlines(keepends=True),
            n=context_len,
        )
    )


# Check if the computed diff is equivalent to the original diff
def assert_same_diff(original_diff: PatchSet, function_diff: List[str]) -> bool:
    """
    Checks if the computed diff is equivalent to the original diff
    """
    original_source = ""
    original_target = ""
    original_added_lines = []
    original_removed_lines = []
    # Get the original changed lines
    # TODO: this diff is inverted, i.e. the target file is the buggy file
    for file in original_diff:
        for hunk in file:
            for line in hunk:
                if line.is_added:
                    original_removed_lines.append(line.value.strip())
                    original_source += line.value
                elif line.is_removed:
                    original_added_lines.append(line.value.strip())
                    original_target += line.value
                elif line.is_context:
                    original_source += line.value
                    original_target += line.value
    # Get the new changed lines
    new_source = ""
    new_target = ""
    new_added_lines = []
    new_removed_lines = []
    for line in function_diff:
        if any(line.startswith(x) for x in ["---", "+++", "@@"]):
            continue
        elif line.startswith("+"):
            new_added_lines.append(line[1:].strip())
            new_target += line[1:]
        elif line.startswith("-"):
            new_removed_lines.append(line[1:].strip())
            new_source += line[1:]
        else:
            new_source += line[1:]
            new_target += line[1:]
    # Check that all the
    if (
        any([line not in original_source for line in new_removed_lines])
        or any([line not in original_target for line in new_added_lines])
        or any([line not in new_source for line in original_removed_lines])
        or any([line not in new_target for line in original_added_lines])
    ):
        return False
    return True


def extract_functions(
    bug: Bug,
    fixed: bool = True,
    source_directories: List[str] = ["src", "java_programs"],
) -> List[dict[str, str]]:
    """
    Extracts function from the java files of the bug
    Returns a list of tuples containing (file_path, function_code)
    """
    checkout_path = os.path.join(
        tempfile.gettempdir(), "elleelleaime", bug.get_identifier(), str(uuid4())
    )
    result = []

    try:
        # Checkout the bug
        bug.checkout(checkout_path, fixed=fixed)

        # Iterate over all *.java files
        for source_directory in source_directories:
            for file in Path(checkout_path, source_directory).rglob("*.java"):
                # Read the code
                with open(file, "r", encoding="ISO-8859-1") as f:
                    code = f.read()
                # Find line numbers
                line_numbers = [i for i, line in enumerate(code.split("\n"), 1)]
                # Find functions with javalang
                functions = {}
                for line in line_numbers:
                    try:
                        function = load_origin_code_node(file, [line])[0]
                        if function.hash != "":
                            functions[function.hash] = function
                    except Exception as e:
                        continue
                # Get the code of each function
                for function in functions.values():
                    result.append(
                        {
                            "file_path": file.relative_to(checkout_path),
                            "function_code": find_code(
                                file,
                                [
                                    i
                                    for i in range(
                                        function.start_pos, function.end_pos + 1
                                    )
                                ],
                            ),
                        }
                    )
        return result
    finally:
        # Remove the checked-out bug
        shutil.rmtree(checkout_path, ignore_errors=True)


def extract_single_function(bug: Bug) -> Optional[Tuple[str, str]]:
    """
    Extracts the buggy and fixed code of single-function bugs.
    Returns None is bug is not single-function

    Args:
        bug (Bug): THe bug to extract the code from

    Returns:
        Optional[Tuple[str, str]]: None if the bug is not single-function, otherwise a tuple of the form (buggy_code, fixed_code)
    """
    buggy_path = os.path.join(
        tempfile.gettempdir(), "elleelleaime", bug.get_identifier(), str(uuid4())
    )
    fixed_path = os.path.join(
        tempfile.gettempdir(), "elleelleaime", bug.get_identifier(), str(uuid4())
    )

    try:
        # Checkout the buggy and fixed versions of the bug
        bug.checkout(buggy_path, fixed=False)
        bug.checkout(fixed_path, fixed=True)

        # Note: this diff is inverted, i.e. the target file is the buggy file
        diff = PatchSet(bug.get_ground_truth())

        buggy_file_path = os.path.join(
            buggy_path,
            diff[0].target_file[2:]
            if diff[0].target_file.startswith("b/")
            else diff[0].target_file,
        )
        fixed_file_path = os.path.join(
            fixed_path,
            diff[0].source_file[2:]
            if diff[0].source_file.startswith("a/")
            else diff[0].source_file,
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
                return None

        # Get the buggy and fixed code with line numbers
        # If the ast nodes are not of the correct type, then we have a whole-function removal/addition
        buggy_code = (
            find_code(
                buggy_file_path,
                [i for i in range(buggy_method.start_pos, buggy_method.end_pos + 1)],
            )
            if buggy_method is not None
            else ""
        )
        fixed_code = (
            find_code(
                fixed_file_path,
                [i for i in range(fixed_method.start_pos, fixed_method.end_pos + 1)],
            )
            if fixed_method is not None
            else ""
        )

        # HACK: sometimes we are not able to properly retrieve the code at the function-level
        # This happens in cases suchas Closure-46 where a whole function is removed
        # To detected and circumvent such cases, we check that the function_diff is equivalent to the original diff
        # If the diffs are not equivalent, we try to fix the function diff by setting the fixed_code and buggy_code to empty
        # If on of these works we assume it as correct (since the diff is now equivalent to the original one)
        fdiff = compute_diff(buggy_code, fixed_code)
        if not assert_same_diff(diff, fdiff):
            fdiff = compute_diff(buggy_code, "")
            if assert_same_diff(diff, fdiff):
                fixed_code = ""
            else:
                fdiff = compute_diff("", fixed_code)
                if assert_same_diff(diff, fdiff):
                    buggy_code = ""
                else:
                    return None

        return buggy_code, fixed_code

    finally:
        # Remove the checked-out bugs
        shutil.rmtree(buggy_path, ignore_errors=True)
        shutil.rmtree(fixed_path, ignore_errors=True)


def remove_java_comments(source: str) -> str:
    # Define states
    NORMAL, SINGLE_COMMENT, MULTI_COMMENT, STRING_LITERAL, CHAR_LITERAL = range(5)

    state = NORMAL
    result = []
    i = 0

    while i < len(source):
        # Check the current state and process accordingly
        if state == NORMAL:
            if source[i : i + 2] == "//":
                state = SINGLE_COMMENT
                i += 2
            elif source[i : i + 2] == "/*":
                state = MULTI_COMMENT
                i += 2
            elif source[i] == '"':
                state = STRING_LITERAL
                result.append(source[i])
                i += 1
            elif source[i] == "'":
                state = CHAR_LITERAL
                result.append(source[i])
                i += 1
            else:
                result.append(source[i])
                i += 1
        elif state == SINGLE_COMMENT:
            if source[i] == "\n":
                state = NORMAL
                result.append(source[i])
                i += 1
            else:
                i += 1
        elif state == MULTI_COMMENT:
            if source[i : i + 2] == "*/":
                state = NORMAL
                i += 2
            else:
                i += 1
        elif state == STRING_LITERAL:
            if source[i] == "\\":
                result.append(source[i])
                i += 1
                result.append(source[i])
                i += 1
            elif source[i] == '"':
                state = NORMAL
                result.append(source[i])
                i += 1
            else:
                result.append(source[i])
                i += 1
        elif state == CHAR_LITERAL:
            if source[i] == "\\":
                result.append(source[i])
                i += 1
                result.append(source[i])
                i += 1
            elif source[i] == "'":
                state = NORMAL
                result.append(source[i])
                i += 1
            else:
                result.append(source[i])
                i += 1

    return "".join(result)


def remove_empty_lines(source):
    """Remove all empty lines from Java source code."""
    return re.sub(r"^\s*$\n", "", source, flags=re.MULTILINE)
