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
            if generation is None:
                evaluation.append(
                    {
                        "generation": None,
                        "exact_match": False,
                        "compile": False,
                        "test": False,
                    }
                )
                continue

            buggy_path = os.path.join(
                tempfile.gettempdir(),
                "elleelleaime",
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
                "compile": False,
                "test": False,
            }

            if generation is not None:
                try:
                    # Checkout the buggy code
                    bug.checkout(buggy_path, fixed=False)

                    # Locate and load the buggy file
                    buggy_file_path = bug.get_buggy_file_path(buggy_path)
                    with open(buggy_file_path, "r", encoding="ISO-8859-1") as f:
                        buggy_code = f.read()

                    # Replace the buggy code with the generated code
                    if sample["buggy_code"] not in buggy_code:
                        logging.warning(
                            f"Could not find buggy code in {buggy_file_path} for {sample['identifier']}"
                        )
                    else:
                        buggy_code = buggy_code.replace(
                            sample["buggy_code"], generation
                        )

                        # Write the buggy code to the file
                        with open(
                            buggy_file_path,
                            "w",
                            encoding="ISO-8859-1",
                            errors="replace",
                        ) as f:
                            f.write(buggy_code)
                        # Evaluate the buggy code
                        compilation_result = bug.compile(buggy_path)
                        result["compile"] = compilation_result.is_passing()
                        if result["compile"]:
                            test_result = bug.test(buggy_path)
                            result["test"] = test_result.is_passing()
                finally:
                    bug.cleanup(buggy_path)

            evaluation.append(result)
            if evaluation[-1]["test"]:
                logging.info(f"Found a plausible patch for {sample['identifier']}!")

        return evaluation
