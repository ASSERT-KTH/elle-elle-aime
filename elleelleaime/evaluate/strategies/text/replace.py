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
            buggy_path = os.path.join(
                tempfile.gettempdir(),
                "elleelleaime",
                bug.get_identifier(),
                str(uuid4()),
            )

            result = {
                "generation": generation,
                "exact_match": generation is not None
                and all(
                    [
                        x.strip() == y.strip()
                        for x, y in zip(
                            generation.split("\n"), sample["fixed_code"].split("\n")
                        )
                    ]
                ),
                "compile": False,
                "test": False,
            }

            if generation is not None:
                try:
                    # Note: this diff is inverted, i.e. the target file is the buggy file
                    diff = PatchSet(bug.get_ground_truth())

                    # Checkout the buggy code
                    bug.checkout(buggy_path, fixed=False)

                    # Locate and load the buggy file
                    buggy_file_path = os.path.join(
                        buggy_path,
                        diff[0].target_file[2:]
                        if diff[0].target_file.startswith("b/")
                        else diff[0].target_file,
                    )
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
                        result["compile"] = (
                            compilation_result.is_executing()
                            and compilation_result.is_passing()
                        )
                        if result["compile"]:
                            test_result = bug.test(buggy_path)
                            result["test"] = (
                                test_result.is_executing() and test_result.is_passing()
                            )
                finally:
                    shutil.rmtree(buggy_path)

            evaluation.append(result)
            if evaluation[-1]["test"]:
                logging.info(f"Found a plausible patch for {sample['identifier']}!")

        return evaluation
