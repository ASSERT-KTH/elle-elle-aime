from concurrent.futures import ThreadPoolExecutor, as_completed
from core.utils.jsonl import stream_jsonl, write_jsonl
from core.utils.benchmarks import get_benchmark
from core.utils.jsonl import write_jsonl
from evaluation.registry import EvaluationStrategyRegistry

import fire
import sys
import tqdm
import logging

import fire
import sys
import tqdm
import logging


def entry_point(
    benchmark: str,
    patches_path: str,
    evaluation_strategy: str,
    n_workers: int = 4
):
    """
    Evaluates the generated patches of the given benchmark 
    and writes the results to f"evaluation_{benchmark}_{prompt_strategy}_{model_name}.jsonl.gz"
    """

    # Get the benchmark, check if it exists, and initialize it
    benchmark_obj = get_benchmark(benchmark)
    if benchmark_obj is None:
        raise ValueError(f"Unknown benchmark {benchmark}")
    benchmark_obj.initialize()

    results = []
    
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = []
        
        logging.info("Reading samples...")
        for sample in tqdm.tqdm(stream_jsonl(patches_path)):
            futures.append(executor.submit(evaluate_candidate, sample, benchmark_obj, evaluation_strategy))
        
        logging.info("Generating candidates...")
        for future in tqdm.tqdm(as_completed(futures), total=len(futures)):
            results.append(future.result())

    # Write results to jsonl file
    benchmark = patches_path.split("_")[1]
    prompt_strategy = patches_path.split("_")[2]
    model_name = patches_path.split("_")[3].split(".")[0]
    write_jsonl(f"evaluation_{benchmark}_{prompt_strategy}_{model_name}.jsonl.gz", results)


def main():
    logging.getLogger().setLevel(logging.INFO)
    fire.Fire(entry_point)


sys.exit(main())