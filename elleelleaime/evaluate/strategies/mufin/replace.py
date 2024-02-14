from typing import Optional, List
from pathlib import Path
from uuid import uuid4
import os, tempfile, shutil, logging

from ..strategy import PatchEvaluationStrategy
from elleelleaime.core.benchmarks.bug import Bug


class MufinReplaceEvaluationStrategy(PatchEvaluationStrategy):
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
                        "compile": False,
                        "test": False,
                    }
                )
                continue

            fixed_path = os.path.join(
                tempfile.gettempdir(),
                "elleelleaime",
                bug.get_identifier(),
                str(uuid4()),
            )

            result = {
                "generation": generation,
                "compile": False,
                "test": False,
            }

            try:
                # Checkout the buggy code
                bug.checkout(fixed_path, fixed=True)

                # Locate and load the buggy file
                file_path = Path(fixed_path, sample["file_path"])
                with open(file_path, "r", encoding="ISO-8859-1") as f:
                    fixed_code = f.read()

                # Check that fixed code exists
                if sample["fixed_code"] not in fixed_code:
                    logging.error(
                        f"Could not find buggy code in {file_path} for {sample['identifier']}"
                    )
                    break

                # Get the fixed and candidate code
                candidate_code = fixed_code.replace(sample["fixed_code"], generation)

                # Compute plausible match
                # Write the generated code to the file
                with open(
                    file_path,
                    "w",
                    encoding="ISO-8859-1",
                    errors="replace",
                ) as f:
                    f.write(candidate_code)
                # Evaluate the buggy code
                compilation_result = bug.compile(fixed_path)
                result["compile"] = compilation_result.is_passing()
                if result["compile"]:
                    test_result = bug.test(fixed_path)
                    result["test"] = test_result.is_passing()
                evaluation.append(result)
            finally:
                shutil.rmtree(fixed_path)

        return evaluation
