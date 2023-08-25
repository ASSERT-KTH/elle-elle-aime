from concurrent.futures import ThreadPoolExecutor, as_completed
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.utils.jsonl import stream_jsonl, write_jsonl
from elleelleaime.evaluate.strategies.registry import PatchEvaluationStrategyRegistry

import fire
import sys
import tqdm
import logging


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


def entry_point(
    benchmark: str,
    samples_path: str,
    strategy: str = "replace",
    n_workers: int = 4,
    **kwargs,
):
    """
    Evaluates the candidate patches given the samples,
    and writes the results to f"evaluation_{benchmark}_{prompt_strategy}_{model_name}.jsonl.gz"
    """
    results = []

    # Get the benchmark, check if it exists, and initialize it
    benchmark_obj = get_benchmark(benchmark)
    if benchmark_obj is None:
        raise ValueError(f"Unknown benchmark {benchmark}")
    benchmark_obj.initialize()

    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = []

        logging.info("Reading samples...")
        for sample in tqdm.tqdm(stream_jsonl(samples_path)):
            bug = benchmark_obj.get_bug(sample["identifier"])
            if bug is None:
                raise ValueError(f"Unknown bug {sample['identifier']}")
            futures.append(
                executor.submit(evaluate_candidate, bug, sample, strategy, **kwargs)
            )

        logging.info("Generating candidates...")
        for future in tqdm.tqdm(as_completed(futures), total=len(futures)):
            results.append(future.result())

    # Write results to jsonl file
    benchmark = samples_path.split("_")[1]
    prompt_strategy = samples_path.split("_")[2].split(".")[0]
    model_name = samples_path.split("_")[3].split(".")[0]
    write_jsonl(
        f"evaluation_{benchmark}_{prompt_strategy}_{model_name}.jsonl.gz", results
    )


def main():
    logging.getLogger().setLevel(logging.INFO)
    fire.Fire(entry_point)


if __name__ == "__main__":
    sys.exit(main())
