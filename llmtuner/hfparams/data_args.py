from typing import List, Literal, Optional
from dataclasses import dataclass, field


@dataclass
class DataArguments:
    r"""
    Arguments pertaining to what data we are going to input llms for training and eval.
    """

    data_path: Optional[str] = field(
        default=None, 
        metadata={"help": "Path to the dataset."}
    )
    train_file: Optional[str] = field(
        default=None, 
        metadata={"help": "Training file name."}
    )
    eval_file: Optional[str] = field(
        default=None, 
        metadata={"help": "Evaluation file name."}
    )
    test_file: Optional[str] = field(
        default=None, 
        metadata={"help": "Test file name."}
    )
    cache_path: Optional[str] = field(
        default=None, 
        metadata={"help": "Path to the cache directory."}
    )
    cutoff_len: Optional[int] = field(
        default=1024,
        metadata={"help": "The maximum length of the model inputs after tokenization."}
    )
    num_proc: Optional[int] = field(
        default=4, 
        metadata={"help": "Number of processes to use for data preprocessing."}
    )
    max_samples: Optional[int] = field(
        default=None, 
        metadata={"help": "For debugging purposes, truncate the number of examples for each dataset."}
    )
    ignore_pad_token_for_loss: Optional[bool] = field(
        default=True, 
        metadata={"help": "Whether to ignore the tokens corresponding to padded labels in the loss computation or not."}
    )
