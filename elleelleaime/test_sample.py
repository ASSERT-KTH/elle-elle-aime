from concurrent.futures import ThreadPoolExecutor, as_completed
from core.utils.benchmarks import get_benchmark
from core.utils.jsonl import write_jsonl
from core.benchmarks.bug import Bug
from typing import Optional, Union
from sample.prompting.registry import PromptStrategyRegistry

import fire
import sys
import tqdm
import logging


def generate_sample(bug: Bug, prompt_strategy: str, model_name: str = None, strict_one_hunk: bool = False) -> dict[str, Optional[Union[str, Bug]]]:
    """
    Generates the sample for the given bug with the given prompt strategy.
    """

    prompt_strategy_obj = PromptStrategyRegistry().get_strategy(prompt_strategy)
    prompt = prompt_strategy_obj.prompt(bug, model_name, strict_one_hunk)

    # Check if prompt was generated
    if prompt is None:
        return {
            "identifier": bug.get_identifier(),
            "buggy_code": None,
            "fixed_code": None,
            "prompt_strategy": prompt_strategy,
            "prompt": None,
            "ground_truth": bug.get_ground_truth()
        }
    
    # Unpack the prompt
    buggy_code, fixed_code, prompt = prompt
    return {
        "identifier": bug.get_identifier(),
        "buggy_code": buggy_code,
        "fixed_code": fixed_code,
        "prompt_strategy": prompt_strategy,
        "prompt": prompt,
        "ground_truth": bug.get_ground_truth()
    }


def entry_point(
    benchmark: str,
    prompt_strategy: str,
    model_name: str = None,
    strict_one_hunk: bool = False,
    n_workers: int = 1
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

    futures = []
    # breakpoint()
    # Launch a thread for each bug
    """ I have tested the following bugs:
            Lang-3 : four hunk, each hunk only contains one line, only add code lines
            Lang-10: two hunks, one contains multiple lines and another contains one line, only delete code lines; Error from java_lang.py: Node with name not found
            Lang-12: three hunks, two contians multiple lines, the other contains one line, only add code lines
            Lang-18: two hunks, one contians multiple lines, the other contains one line, both add and delete code lines            
            Lang-44: one hunks, contains multiple lines, only add code lines
            Lang-48: two hunks, one contians multiple lines, the other contains one line, only add code lines
            Chart-1: one hunk, only contains one line, both delete and add code line
           Chart-23: One hunk, add a whole new method. Error from java_lang.py: Node with name equals not found
    """
    for bug in benchmark_obj.get_bugs():
        if bug.get_identifier() == "Chart-23":
            futures.append(generate_sample(bug, prompt_strategy, model_name, strict_one_hunk))
            # args = (bug, prompt_strategy, model_name, strict_one_hunk)
            # futures.append(executor.submit(generate_sample, *args))

    # Check that all bugs are being processed
    assert len(futures) == len(benchmark_obj.get_bugs()), "Some bugs are not being processed"

    # Wait for the results
    for future in tqdm.tqdm(as_completed(futures), total=len(futures)):
        results.append(future.result())

    # Write results to jsonl file
    write_jsonl(f"samples_{benchmark}_{prompt_strategy}.jsonl.gz", results)


def main():
    logging.getLogger().setLevel(logging.INFO)
    fire.Fire(entry_point)


sys.exit(main())