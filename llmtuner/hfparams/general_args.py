from typing import Literal, Optional
from dataclasses import dataclass, field


@dataclass
class GeneralArguments:
    r"""
    Arguments pertaining to which stage we are going to perform.
    """
    stage: Optional[Literal["pt", "sft"]] = field(
        default="sft",
        metadata={"help": "Which stage will be performed in training."}
    )
