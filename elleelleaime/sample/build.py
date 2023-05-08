from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from elleelleaime.core.utils.utils import get_benchmark
from elleelleaime.core.utils.jsonl import write_jsonl
from elleelleaime.sample.sample_generation import generate_sample

import fire
import sys
import tqdm
import logging


def entry_point(
    benchmark: str,
    prompt_strategy: str,
    n_workers: int = 4
):
    """
    Generates the test samples for the bugs of the given benchmark with the given
    prompt strategy, and writes the results to f"samples_{dataset}_{prompt_strategy}.jsonl.gz"
    """

    # Get the benchmark, check if it exists, and initialize it
    benchmark_obj = get_benchmark(benchmark)
    if benchmark_obj is None:
        raise ValueError(f"Unknown benchmark {benchmark}")
    benchmark_obj.initialize()

    # Generate the prompts in parallel
    logging.info("Building the prompts...")
    results = []

    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = []

        # Launch a thread for each bug
        for bug in benchmark_obj.get_bugs():
            args = (bug, prompt_strategy)
            futures.append(executor.submit(generate_sample, *args))
            break

        # Check that all bugs are being processed
        #assert len(futures) == len(benchmark_obj.get_bugs()), "Some bugs are not being processed"

        # Wait for the results
        for future in tqdm.tqdm(as_completed(futures), total=len(futures)):
            results.append(future.result())

    # Write results to jsonl file
    write_jsonl(f"samples_{benchmark}_{prompt_strategy}.jsonl.gz", results)

def main():
    logging.getLogger().setLevel(logging.INFO)
    fire.Fire(entry_point)


sys.exit(main())