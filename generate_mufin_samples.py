from concurrent.futures import ThreadPoolExecutor, as_completed
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.utils.jsonl import write_jsonl
from elleelleaime.core.benchmarks.bug import Bug
from typing import Optional, Union, List
from elleelleaime.sample.mufin.registry import MufinStrategyRegistry

import fire
import traceback
import sys
import tqdm
import logging


def generate_mufin_samples(
    bug: Bug, sample_strategy: str, **kwargs
) -> List[dict[str, Optional[str]]]:
    """
    Generates the sample for the given bug with the given prompt strategy.
    """
    sample_strategy_obj = MufinStrategyRegistry.get_strategy(sample_strategy, **kwargs)
    return sample_strategy_obj.sample(bug)


def entry_point(
    benchmark: str,
    sample_strategy: str,
    n_workers: int = 1,
    **kwargs,
):
    """
    Generates the samples for the bugs of the given benchmark with the given
    sampling strategy, and writes the results to f"samples_{dataset}_{sample_strategy}.jsonl.gz"
    """

    # Get the benchmark, check if it exists, and initialize it
    benchmark_obj = get_benchmark(benchmark)
    if benchmark_obj is None:
        raise ValueError(f"Unknown benchmark {benchmark}")
    benchmark_obj.initialize()

    # Generate the samples in parallel
    logging.info("Building the samples...")
    results = {}

    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = []

        # Launch a thread for each bug
        future_to_bug = {}
        for bug in benchmark_obj.get_bugs():
            future = executor.submit(
                generate_mufin_samples, bug, sample_strategy, **kwargs
            )
            future_to_bug[future] = bug
            futures.append(future)

        # Check that all bugs are being processed
        assert len(futures) == len(
            benchmark_obj.get_bugs()
        ), "Some bugs are not being processed"

        # Wait for the results
        for future in tqdm.tqdm(as_completed(futures), total=len(futures)):
            try:
                # Get result and check if not already in hash (dedepuplicate)
                samples = future.result()
                for sample in samples:
                    if sample["hash"] not in results:
                        results[sample["hash"]] = sample
            except Exception as e:
                logging.error(
                    f"Error while generating sample for bug {future_to_bug[future]}: {traceback.format_exc()}"
                )

    # Write results to jsonl file
    kwargs_str = "_".join([f"{key}_{value}" for key, value in kwargs.items()])
    write_jsonl(
        f"samples_{benchmark}_{sample_strategy}_{kwargs_str}.jsonl.gz",
        list(results.values()),
    )


def main():
    logging.getLogger().setLevel(logging.INFO)
    fire.Fire(entry_point)


if __name__ == "__main__":
    sys.exit(main())
