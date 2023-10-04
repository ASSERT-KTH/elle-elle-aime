from typing import Optional, Dict
from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.utils.benchmarks import get_benchmark
from datasets import load_dataset, Dataset
from pathlib import Path
from uuid import uuid4
from transformers import AutoTokenizer

import fire
import sys
import tqdm
import logging
import tempfile
import numpy as np


def checkout_oldest(dataset: str, project: Optional[str] = None) -> Dict[str, Bug]:
    """
    Checks out the oldest bug in the given project.
    """
    benchmark = get_benchmark(dataset)
    if benchmark == None:
        raise ValueError("Unknown dataset %s" % dataset)

    bugs = benchmark.get_oldest_bug(project)
    return bugs


def extract_training_data(
    bug: Bug, output_path: str, push_to_hub: bool = False
) -> None:
    checkout_path = str(
        Path(tempfile.gettempdir(), "elleelleaime", bug.get_identifier(), str(uuid4()))
    )

    # We checkout the oldest version of each bug, so that there is no leakage
    bug.checkout(checkout_path, fixed=False)

    # Find all java files in the checkout path
    extensions = [".java", ".md", ".txt", "README"]
    files = []
    for extension in extensions:
        files.extend(
            [
                str(path)
                for path in Path(checkout_path).rglob(f"*{extension}")
                if path.is_file()
            ]
        )

    # Load as a dataset
    dataset = load_dataset(
        "text", data_files=files, encoding="ISO-8859-1", sample_by="document"
    )

    # Push dataset to huggingface
    if push_to_hub:
        dataset.push_to_hub(f"ASSERT-KTH/{bug.get_identifier()}", private=True)

    # TODO: do near-deduplication of the files
    # TODO: Long-line filter
    # TODO: Alpha-numeric filter
    # TODO: XML filter
    # TODO: JSON YAML filter

    # Tokenize the files
    context_length = 2048
    tokenizer = AutoTokenizer.from_pretrained("codellama/CodeLlama-7b-hf")
    tokenizer.pad_token = tokenizer.eos_token

    # Tokenize each file at full lenght
    def tokenize(batch):
        outputs = tokenizer(
            batch["text"],
            truncation=False,
        )
        input_batch = []
        for input_ids in outputs["input_ids"]:
            input_batch.append(input_ids)
        return {"input_ids": input_batch}

    tokenized_dataset = dataset.map(
        tokenize, batched=True, remove_columns=dataset["train"].column_names
    )

    # Concatenate the files into a single sequence of tokens
    # Each file is separated by a special token (tokenizer.eos_token)
    concatenation = np.array([])
    for sample in tqdm.tqdm(tokenized_dataset["train"]):
        concatenation = np.append(
            concatenation, sample["input_ids"] + [tokenizer.eos_token_id]
        )

    # Split the concatenation into chunks of context_length
    total_chunks = len(concatenation) // context_length
    chunks = np.array_split(
        concatenation[: total_chunks * context_length], total_chunks
    )
    chunked_dataset = Dataset.from_dict({"input_ids": chunks})


def entry_point(
    output_path: str,
    dataset: str = "defects4j",
    project: Optional[str] = None,
    push_to_hub: bool = False,
    **kwargs,
):
    """
    Extracts project-specific information for a pre-training run.
    """
    # Get the oldest bugs for each project
    oldest_bug = checkout_oldest(dataset, project)

    # Extract training data for each project
    # TODO: make this parallel
    for pid in tqdm.tqdm(oldest_bug, "Extracting training data for each project"):
        bug = oldest_bug[pid]
        extract_training_data(bug, str(Path(output_path, pid)), push_to_hub=push_to_hub)


def main():
    logging.getLogger().setLevel(logging.INFO)
    fire.Fire(entry_point)


if __name__ == "__main__":
    sys.exit(main())
