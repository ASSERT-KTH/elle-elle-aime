from concurrent.futures import ThreadPoolExecutor, as_completed
from elleelleaime.core.utils.benchmarks import get_benchmark, Benchmark
from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.utils.jsonl import stream_jsonl, write_jsonl, write_json
from elleelleaime.evaluate.strategies.registry import PatchEvaluationStrategyRegistry

import fire
import sys
import tqdm
import logging
import os

from typing import List

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


def test(evaluation: dict) -> bool:
    """
    Returns True if the evaluation is plausible.
    """
    return evaluation["compile"] and evaluation["test"]


def compilable(evaluation: dict) -> bool:
    """
    Returns True if the evaluation is compilable.
    """
    return evaluation["compile"]

def fail_fail(evaluation: dict) -> bool:
    """
    Returns True if the evaluation is a fail-fail.
    """
    return not evaluation["compile"] and not evaluation["test"]

def pass_fail(evaluation: dict) -> bool:
    """
    Returns True if the evaluation is a pass-fail.
    """
    return evaluation["compile"] and not evaluation["test"]

def pass_pass(evaluation: dict) -> bool:
    """
    Returns True if the evaluation is a pass-pass.
    """
    return evaluation["compile"] and evaluation["test"]

def correctness_evaluation(benchmark_obj: Benchmark, samples: List, strategy: str, n_workers: int, **kwargs) -> List[dict]:
    logging.info("Evaluating correctness...")
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
        return results


def compute_statistics(samples: List[dict]) -> dict:
    logging.info("Computing statistics...")
    statistics = {
        "samples": 0,
        "samples_with_prompts": 0,
        "fail_fail": 0,
        "pass_fail": 0,
        "pass_pass": 0,
        "compilable": 0,
        "test": 0,
    }
    for sample in samples:
        statistics["samples"] += 1
        statistics["samples_with_prompts"] += 1 if "prompt" in sample and sample["prompt"] is not None else 0
        for evaluation in sample["evaluation"]:
            statistics["fail_fail"] += fail_fail(evaluation)
            statistics["pass_fail"] += pass_fail(evaluation)
            statistics["pass_pass"] += pass_pass(evaluation)
            statistics["compilable"] += compilable(evaluation)
            statistics["test"] += test(evaluation)
            
    return statistics


def entry_point(
    benchmark: str,
    samples_path: str,
    strategy: str = "mufin-replace",
    n_workers: int = 4,
    correctness: bool = True,
    **kwargs,
):
    """
    Evaluates the candidate patches given the samples,
    and writes the results to f"evaluation_{benchmark}_{prompt_strategy}_{model_name}.jsonl.gz"
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
        samples = correctness_evaluation(benchmark_obj, samples, strategy, n_workers, **kwargs)

    # Statistics
    if kwargs.get("statistics", False):
        statistics = compute_statistics(samples)
        
        # Write statistics to file
        write_json(
            os.path.join(
                dir_path, f"statistics_{benchmark}_{prompt_strategy}_{model_name}.json"
            ),
            statistics,
        )
        
    # Write results to jsonl file
    write_jsonl(
        os.path.join(
            dir_path, f"evaluation_{benchmark}_{prompt_strategy}_{model_name}.jsonl.gz"
        ),
        samples,
    )


def main():
    logging.getLogger().setLevel(logging.INFO)
    fire.Fire(entry_point)


if __name__ == "__main__":
    sys.exit(main())
