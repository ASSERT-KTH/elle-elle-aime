from typing import Optional, List
from unidiff import PatchSet
from uuid import uuid4
import os, tempfile, shutil, logging

from ..strategy import PatchEvaluationStrategy
from elleelleaime.core.benchmarks.bug import Bug


class ReplaceEvaluationStrategy(PatchEvaluationStrategy):
    """
    Implements the zero-shot cloze style prompt strategy for single diff file.
    """

    def __init__(self, **kwargs):
        super().__init__()

    def _evaluate_impl(self, bug: Bug, sample: dict) -> Optional[List[dict]]:
        """
        Returns the evaluation for the given bug and sample.

        :param bug: The bug to generate the prompt for.
        :param sample: The sample to evaluate.
        """
        evaluation = []

        for generation in sample["generation"]:
            # If the generation is None, we skip the evaluation
            if generation is None:
                evaluation.append(
                    {
                        "generation": None,
                        "exact_match": False,
                        "ast_match": False,
                        "compile": False,
                        "test": False,
                    }
                )
                continue

            buggy_path = os.path.join(
                tempfile.gettempdir(),
                f"elleelleaime-{os.getlogin()}",
                bug.get_identifier(),
                str(uuid4()),
            )

            # Remove comments and empty lines from the generated code and the fixed code
            generation_no_comments = [
                line
                for line in generation.splitlines(keepends=True)
                if not line.strip().startswith("//") and not line.strip() == ""
            ]

            fixed_code = [
                line
                for line in sample["fixed_code"].splitlines(keepends=True)
                if not line.strip().startswith("//") and not line.strip() == ""
            ]

            result = {
                "generation": generation,
                "exact_match": all(
                    [
                        x.strip() == y.strip()
                        for x, y in zip(generation_no_comments, fixed_code)
                    ]
                ),
                "ast_match": False,
                "compile": False,
                "test": False,
            }

            # If the generation is an exact match, there is no need to evaluate the AST, compile or test
            if result["exact_match"]:
                result["ast_match"] = True
                result["compile"] = True
                result["test"] = True
                evaluation.append(result)
                continue

            try:
                # Note: this diff is inverted, i.e. the target file is the buggy file
                diff = PatchSet(bug.get_ground_truth())

                # Checkout the buggy code
                bug.checkout(buggy_path, fixed=False)

                # Locate and load the buggy file
                if bug.is_ground_truth_inverted():
                    buggy_file_path = os.path.join(
                        buggy_path,
                        (
                            diff[0].target_file[2:]
                            if diff[0].target_file.startswith("b/")
                            else diff[0].target_file
                        ),
                    )
                else:
                    buggy_file_path = os.path.join(
                        buggy_path,
                        (
                            diff[0].source_file[2:]
                            if diff[0].source_file.startswith("a/")
                            else diff[0].source_file
                        ),
                    )

                with open(buggy_file_path, "r", encoding="ISO-8859-1") as f:
                    buggy_code = f.read()

                # Check that buggy code exists
                if sample["buggy_code"] not in buggy_code:
                    logging.error(
                        f"Could not find buggy code in {buggy_file_path} for {sample['identifier']}"
                    )
                    break

                # Get the fixed and candidate code
                fixed_code = buggy_code.replace(
                    sample["buggy_code"], sample["fixed_code"]
                )
                candidate_code = buggy_code.replace(sample["buggy_code"], generation)

                # Compute plausible match
                # Write the generated code to the file
                with open(
                    buggy_file_path,
                    "w",
                    encoding="ISO-8859-1",
                    errors="replace",
                ) as f:
                    f.write(candidate_code)

                # Evaluate the buggy code
                compilation_result = bug.compile(buggy_path)
                result["compile"] = compilation_result.is_passing()
                # If it compiles, test the code
                if result["compile"] or result["compile"] is None:
                    test_result = bug.test(buggy_path)
                    result["test"] = test_result.is_passing()
                    # If the tests pass, check if the ASTs match
                    # Note: we do not for AST matching before because the ast matcher returns false positives in some cases
                    if result["test"]:
                        result["ast_match"] = self.ast_match(fixed_code, candidate_code)
                evaluation.append(result)
            finally:
                shutil.rmtree(buggy_path)

        return evaluation
