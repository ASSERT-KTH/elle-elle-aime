from concurrent.futures import ThreadPoolExecutor
from core.utils.jsonl import stream_jsonl, write_jsonl
from strategies.registry import PatchGenerationStrategyRegistry

import fire
import sys
import tqdm
import logging


def generate_candidate(sample: dict, model_name: str) -> dict:
    """
    Generates the candidate patch for the given sample and model.
    """
    
    generation_strategy = PatchGenerationStrategyRegistry().get_generation(model_name)
    generation = generation_strategy.generate(sample["prompt"])
    sample["generation"] = generation

    return sample


def entry_point(
    samples_path: str,
    model_name: str,
    n_workers: int = 4
):
    """
    Generates the candidate patches given the samples and the model,
    and writes the results to f"candidates_{dataset}_{prompt_strategy}_{model_name}.jsonl.gz"
    """
    results = []
    
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = []
        
        logging.info("Reading samples...")
        for sample in tqdm.tqdm(stream_jsonl(samples_path)):
            futures.append(executor.submit(generate_candidate, sample, model_name))
        
        logging.info("Generating candidates...")
        for future in tqdm.tqdm(futures):
            results.append(future.result())

    # Write results to jsonl file
    dataset = samples_path.split("_")[1]
    prompt_strategy = samples_path.split("_")[2].split(".")[0]
    write_jsonl(f"candidates_{dataset}_{prompt_strategy}_{model_name}.jsonl.gz", results)


def main():
    logging.getLogger().setLevel(logging.INFO)
    fire.Fire(entry_point)


sys.exit(main())