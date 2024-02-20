from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

from elleelleaime.core.utils.jsonl import stream_jsonl, write_jsonl
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.process.mufin.registry import MufinStrategyRegistry

import fire
import sys
import tqdm
import logging
import os


def process_sample(
    sample: dict, strategy: str, **kwargs
) -> List[dict[str, Optional[str]]]:
    process_strategy = MufinStrategyRegistry().get_strategy(strategy, **kwargs)
    return process_strategy.process(sample)


def entry_point(
    benchmark: str,
    samples_path: str,
    strategy: str = "mufin",
    n_workers: int = 4,
    **kwargs,
):
    """
    Processes the samples and writes the results to f"training_{benchmark}_{prompt_strategy}_{model_name}.jsonl.gz"
    """
    # Get the benchmark, check if it exists, and initialize it
    samples_file_name = os.path.basename(samples_path)
    dir_path = os.path.dirname(samples_path)
    prompt_strategy = samples_file_name.split("_")[2].split(".")[0]
    model_name = samples_file_name.split("_")[3].split(".")[0]

    # Read the samples
    logging.info("Reading samples...")
    samples = list(stream_jsonl(samples_path))

    # Process the samples
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = []
        for sample in tqdm.tqdm(samples):
            futures.append(executor.submit(process_sample, sample, strategy, **kwargs))

        logging.info("Waiting for samples...")
        samples = []
        for future in tqdm.tqdm(as_completed(futures), total=len(futures)):
            samples.extend(future.result())

    # Write results to jsonl file
    logging.info("Writing results to jsonl file...")
    kwargs_str = "-".join([f"{k}={v}" for k, v in kwargs.items()])
    write_jsonl(
        os.path.join(
            dir_path, f"training_{benchmark}_{prompt_strategy}_{model_name}_{kwargs_str}.jsonl"
        ),
        samples,
    )


def main():
    logging.getLogger().setLevel(logging.INFO)
    fire.Fire(entry_point)


if __name__ == "__main__":
    sys.exit(main())
