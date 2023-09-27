from typing import TYPE_CHECKING, Any, Dict, List, Optional

# from llmtuner.tuner.core import get_train_args, load_model_and_tokenizer
from llmtuner.tuner.core import get_train_args
# from llmtuner.tuner.pt import run_pt 
# from llmtuner.tuner.sft import run_sft


if TYPE_CHECKING:
    from transformers import TrainerCallback


def run_exp(
    args: Optional[Dict[str, Any]] = None,
    callbacks: Optional[List["TrainerCallback"]] = None,      
):
    model_args, data_args, training_args, fine_args, generating_args, general_args = get_train_args(args)

    # Test
    breakpoint()
    print("model_args:", model_args)


if __name__ == "__main__":
    run_exp()