from concurrent.futures import ThreadPoolExecutor, as_completed
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.utils.jsonl import stream_jsonl, write_jsonl
from elleelleaime.evaluate.strategies.registry import PatchEvaluationStrategyRegistry

from pathlib import Path

import numpy as np
import uuid
import fire
import shutil
import sys
import tqdm
import logging
import json
import os
import tempfile
import subprocess


def evaluate_candidate(bug: Bug, sample: dict, strategy: str, **kwargs) -> dict:
    """
    Evaluates the candidate patch for the given sample.
    """

    evaluation_strategy = PatchEvaluationStrategyRegistry(**kwargs).get_evaluation(
        strategy
    )
    evaluation = evaluation_strategy.evaluate(bug, sample)
    sample["evaluation"] = evaluation

    return sample


def exact_match(evaluation: dict) -> bool:
    """
    Returns True if the evaluation is an exact match.
    """
    return bool(evaluation["exact_match"])


def ast_match(evaluation: dict) -> bool:
    """
    Returns True if the evaluation is an AST match.
    """
    return bool(evaluation["ast_match"])


def plausible(evaluation: dict) -> bool:
    """
    Returns True if the evaluation is plausible.
    """
    return bool(evaluation["test"])


def compilable(evaluation: dict) -> bool:
    """
    Returns True if the evaluation is compilable.
    """
    return bool(evaluation["compile"])


def compute_diff(buggy_code: str, fixed_code: str, context_len: int = 3) -> str:
    """
    Computes the diff between the buggy and fixed code.
    """
    buggy_path = Path(tempfile.gettempdir(), f"{uuid.uuid4()}_buggy.java")
    with open(buggy_path, "w") as f:
        f.write(buggy_code)

    fixed_path = Path(tempfile.gettempdir(), f"{uuid.uuid4()}_fixed.java")
    with open(fixed_path, "w") as f:
        f.write(fixed_code)

    # we want to ignore whitespace changes with -w which does not exist in difflib.unified_diff
    # with git diff, we even get the name of the changed function in the diff, which helps a lot
    cmd = f"git diff --patience -U{context_len} -w {buggy_path} {fixed_path}"
    run = subprocess.run(cmd, shell=True, capture_output=True)
    return run.stdout.decode("utf-8")


def pass_at_k(n: int, c: int, k: int):
    """
    :param n: total number of samples
    :param c: number of correct samples
    :param k: k in pass@$k$
    """
    if n - c < k:
        return 1.0
    else:
        return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))


def compute_statistics(samples: list) -> dict:
    """
    Computes statistics over the evaluation.
    """
    statistics = {
        "num_bugs": 0,
        "num_bugs_with_prompt": 0,
        "num_bugs_with_candidates": 0,
        "num_bugs_with_exact_match_candidates": 0,
        "num_bugs_with_ast_match_candidates": 0,
        "num_bugs_with_plausible_candidates": 0,
        "num_bugs_with_compilable_candidates": 0,
        "num_patches": 0,
        "num_compilable_patches": 0,
        "num_plausible_patches": 0,
        "num_ast_match_patches": 0,
        "num_exact_match_patches": 0,
        "bugs_with_exact_match_candidates": [],
        "bugs_with_ast_match_candidates": [],
        "bugs_with_plausible_candidates": [],
        "bugs_with_compilable_candidates": [],
    }

    for sample in tqdm.tqdm(samples):
        statistics["num_bugs"] += 1
        if sample["prompt"]:
            statistics["num_bugs_with_prompt"] += 1
        if sample["generation"] and any(
            candidate["generation"] for candidate in sample["evaluation"]
        ):
            statistics["num_bugs_with_candidates"] += 1
            statistics["num_patches"] += sum(
                bool(candidate["generation"]) for candidate in sample["evaluation"]
            )
            statistics["num_compilable_patches"] += sum(
                compilable(candidate) for candidate in sample["evaluation"]
            )
            statistics["num_plausible_patches"] += sum(
                plausible(candidate) for candidate in sample["evaluation"]
            )
            statistics["num_ast_match_patches"] += sum(
                ast_match(candidate) for candidate in sample["evaluation"]
            )
            statistics["num_exact_match_patches"] += sum(
                exact_match(candidate) for candidate in sample["evaluation"]
            )
            if any(exact_match(candidate) for candidate in sample["evaluation"]):
                statistics["num_bugs_with_exact_match_candidates"] += 1
                statistics["bugs_with_exact_match_candidates"].append(
                    sample["identifier"]
                )
            if any(ast_match(candidate) for candidate in sample["evaluation"]):
                statistics["num_bugs_with_ast_match_candidates"] += 1
                statistics["bugs_with_ast_match_candidates"].append(
                    sample["identifier"]
                )
            if any(compilable(candidate) for candidate in sample["evaluation"]):
                statistics["num_bugs_with_compilable_candidates"] += 1
                statistics["bugs_with_compilable_candidates"].append(
                    sample["identifier"]
                )
            if any(plausible(candidate) for candidate in sample["evaluation"]):
                statistics["num_bugs_with_plausible_candidates"] += 1
                statistics["bugs_with_plausible_candidates"].append(
                    sample["identifier"]
                )

    # geometric progression over k
    for k in [1, 10, 100]:
        if k < statistics["num_bugs_with_prompt"]:
            statistics[f"exact_match@{k}"] = pass_at_k(
                statistics["num_patches"],
                statistics["num_exact_match_patches"],
                k,
            )
            statistics[f"ast_match@{k}"] = pass_at_k(
                statistics["num_patches"],
                statistics["num_ast_match_patches"],
                k,
            )
            statistics[f"plausible@{k}"] = pass_at_k(
                statistics["num_patches"],
                statistics["num_plausible_patches"],
                k,
            )
            statistics[f"compilable@{k}"] = pass_at_k(
                statistics["num_patches"],
                statistics["num_compilable_patches"],
                k,
            )

    statistics["bugs_with_exact_match_candidates"].sort()
    statistics["bugs_with_ast_match_candidates"].sort()
    statistics["bugs_with_plausible_candidates"].sort()
    statistics["bugs_with_compilable_candidates"].sort()

    return statistics


def export_patches(samples: list, dir_path: str) -> None:
    """
    Exports the patches to text files in structured directories.
    """
    # Remove the existing patches directory
    patches_dir = os.path.join(dir_path, "patches")
    if os.path.exists(patches_dir):
        shutil.rmtree(patches_dir)

    for sample in tqdm.tqdm(samples):
        if not sample["generation"] or all(
            candidate["generation"] is None for candidate in sample["evaluation"]
        ):
            continue

        # Write prompt, target diff to file
        target_diff = compute_diff(
            sample["buggy_code"],
            sample["fixed_code"],
            context_len=max(
                len(sample["buggy_code"].splitlines()),
                len(sample["fixed_code"].splitlines()),
            ),
        )

        sample_dir = os.path.join(patches_dir, sample["identifier"])
        os.makedirs(sample_dir, exist_ok=True)

        with open(os.path.join(sample_dir, "target.diff"), "w") as f:
            f.writelines(target_diff)

        with open(os.path.join(sample_dir, "prompt.txt"), "w") as f:
            f.write(sample["prompt"])

        for i, candidate in enumerate(sample["evaluation"]):
            if not candidate["generation"]:
                continue

            # Compute diff between generated code and buggy code
            diff = compute_diff(
                sample["buggy_code"],
                candidate["generation"],
                context_len=max(
                    len(sample["buggy_code"].splitlines()),
                    len(candidate["generation"].splitlines()),
                ),
            )

            # Store in the most restrictive sub-directory
            if exact_match(candidate):
                sub_dir = "exact_match"
            elif ast_match(candidate):
                sub_dir = "ast_match"
            elif plausible(candidate):
                sub_dir = "plausible"
            elif compilable(candidate):
                sub_dir = "compilable"
            else:
                sub_dir = "non_compilable"

            candidate_dir = os.path.join(sample_dir, sub_dir)
            os.makedirs(candidate_dir, exist_ok=True)

            with open(os.path.join(candidate_dir, f"{i}.diff"), "w") as f:
                f.writelines(diff)


def export_bugs(samples, dir_path):
    """
    Exports list of bugs considered in each category to text files.
    """
    bugs_with_prompt = sorted(
        [sample["identifier"] for sample in samples if sample["prompt"] is not None]
    )
    bugs_with_candidates = sorted(
        [
            sample["identifier"]
            for sample in samples
            if sample["generation"] is not None
            and len(sample["generation"]) > 0
            and not all(
                candidate["generation"] is None for candidate in sample["evaluation"]
            )
        ]
    )

    with open(os.path.join(dir_path, "bugs_with_prompt.txt"), "w") as f:
        f.write("\n".join(bugs_with_prompt))

    with open(os.path.join(dir_path, "bugs_with_candidates.txt"), "w") as f:
        f.write("\n".join(bugs_with_candidates))


def entry_point(
    benchmark: str,
    samples_path: str,
    strategy: str = "replace",
    n_workers: int = 4,
    correctness: bool = True,
    **kwargs,
):
    """
    Evaluates the candidate patches given the samples,
    and writes the results to f"evaluation_{benchmark}_{prompt_strategy}_{model_name}.jsonl"

    There are several modes to run this script:
        - Correctness: correctness=True (default) evaluates the candidate patches for correctness with the given strategy.
        - Statistics: statistics=True computes statistics over the evaluation.
        - Export: export=True exports the patches to text files in structured directories.
    """
    # Get the benchmark, check if it exists, and initialize it
    samples_file_name = os.path.basename(samples_path)
    dir_path = os.path.dirname(samples_path)
    prompt_strategy = samples_file_name.split("_")[2].split(".")[0]
    model_name = samples_file_name.split("_")[3].split(".")[0]
    benchmark_obj = get_benchmark(benchmark)
    if benchmark_obj is None:
        raise ValueError(f"Unknown benchmark {benchmark}")
    benchmark_obj.initialize()

    # Read the samples
    logging.info("Reading samples...")
    samples = list(stream_jsonl(samples_path))

    # Correctness evaluation
    if correctness:
        with ThreadPoolExecutor(max_workers=n_workers) as executor:
            futures = []
            for sample in tqdm.tqdm(samples):
                bug = benchmark_obj.get_bug(sample["identifier"])
                if bug is None:
                    raise ValueError(f"Unknown bug {sample['identifier']}")
                futures.append(
                    executor.submit(evaluate_candidate, bug, sample, strategy, **kwargs)
                )

            logging.info("Evaluating candidates...")
            results = []
            for future in tqdm.tqdm(as_completed(futures), total=len(futures)):
                results.append(future.result())
            samples = results

    # Compute statistics over the evaluation
    if "statistics" in kwargs and kwargs["statistics"]:
        # Compute statistics for all samples
        statistics = compute_statistics(samples)
        with open(
            os.path.join(
                dir_path, f"statistics_{benchmark}_{prompt_strategy}_{model_name}.json"
            ),
            "w",
        ) as f:
            json.dump(statistics, f, indent=4)

    # Export patches to text files in structured directories
    if "export" in kwargs and kwargs["export"]:
        export_patches(samples, dir_path)
        export_bugs(samples, dir_path)

    # Write results to jsonl file
    write_jsonl(
        os.path.join(
            dir_path, f"evaluation_{benchmark}_{prompt_strategy}_{model_name}.jsonl"
        ),
        samples,
    )


def main():
    logging.getLogger().setLevel(logging.INFO)
    fire.Fire(entry_point)


if __name__ == "__main__":
    sys.exit(main())
