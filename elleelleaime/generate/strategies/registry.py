from elleelleaime.generate.strategies.strategy import PatchGenerationStrategy
from elleelleaime.generate.strategies.models.openai.openai import (
    OpenAIChatCompletionModels,
)
from elleelleaime.generate.strategies.models.huggingface.incoder import (
    IncoderHFModels,
)
from elleelleaime.generate.strategies.models.huggingface.codellama import (
    CodeLlamaHFModels,
)
from elleelleaime.generate.strategies.models.huggingface.starcoder import (
    StarCoderHFModels,
)
from elleelleaime.generate.strategies.models.huggingface.codellama_lora import (
    CodeLlamaLoRAHFModels,
)

from typing import Tuple


class PatchGenerationStrategyRegistry:
    """
    Class for storing and retrieving models based on their name.
    """

    # The registry is a dictionary of model names to a tuple of the model class and the model's constructor arguments
    # NOTE: Do not instantiate the model here, as we should only instanciate the class to be used
    __MODELS: dict[str, Tuple[type, Tuple]] = {
        # OpenAI models
        "gpt-3.5-turbo": (OpenAIChatCompletionModels, ("gpt-3.5-turbo",)),
        # HuggingFace models
        "incoder-1b": (IncoderHFModels, ("facebook/incoder-1B",)),
        "incoder-6b": (IncoderHFModels, ("facebook/incoder-6B",)),
        "codellama-7b": (CodeLlamaHFModels, ("codellama/CodeLlama-7b-hf",)),
        "codellama-13b": (CodeLlamaHFModels, ("codellama/CodeLlama-13b-hf",)),
        "codellama-7b-instruct": (
            CodeLlamaHFModels,
            ("codellama/CodeLlama-7b-Instruct-hf",),
        ),
        "codellama-13b-instruct": (
            CodeLlamaHFModels,
            ("codellama/CodeLlama-13b-Instruct-hf",),
        ),
        "starcoderbase": (
            StarCoderHFModels,
            ("bigcode/starcoderbase",),
        ),
        "starcoder": (
            StarCoderHFModels,
            ("bigcode/starcoder",),
        ),
        "starcoderplus": (
            StarCoderHFModels,
            ("bigcode/starcoderplus",),
        ),
        # TODO: make this a regex
        "repairllama13b-ftf-full-5k-1epoch": (
            CodeLlamaHFModels,
            ("ASSERT-KTH/RepairLlama13B-ftf-full-5k-1epoch",),
        ),
        "repairllama13b-ftf-full-5k-labelall-1epoch": (
            CodeLlamaHFModels,
            ("ASSERT-KTH/RepairLlama13B-ftf-full-5k-labelall-1epoch",),
        ),
        "codellama7b-closure-ftf-5k": (
            CodeLlamaHFModels,
            ("/proj/berzelius-2023-175/users/x_andaf/training_logs/codellama7b-closure-ftf-5k",)
        ),
        "codellama7b-closure-25epochs-5k": (
            CodeLlamaHFModels,
            ("/proj/berzelius-2023-175/users/x_andaf/training_logs/codellama7b-closure-25epochs-5k",)
        ),
        "codellama7b-closure-25epochs": (
            CodeLlamaHFModels,
            ("/proj/berzelius-2023-175/users/x_andaf/training_logs/codellama7b-closure-25epochs",)
        ),
        "codellama7b-databind-25epochs-5k": (
            CodeLlamaHFModels,
            ("/proj/berzelius-2023-175/users/x_andaf/training_logs/codellama7b-databind-25epochs-5k",)
        ),
        "codellama7b-databind-25epochs": (
            CodeLlamaHFModels,
            ("/proj/berzelius-2023-175/users/x_andaf/training_logs/codellama7b-databind-25epochs",)
        ),
        "codellama7b-closure-fim-gradientac": (
            CodeLlamaHFModels,
            ("/proj/berzelius-2023-175/users/x_andaf/training_logs/codellama7b-closure-fim-gradientac",)
        ),
        "codellama7b-closure-fim-gradientac": (
            CodeLlamaHFModels,
            ("/proj/berzelius-2023-175/users/x_andaf/training_logs/codellama7b-closure-fim-gradientac",)
        ),
        "codellama7b-closure-fim-gac-llr": (
            CodeLlamaHFModels,
            ("/proj/berzelius-2023-175/users/x_andaf/training_logs/codellama7b-closure-fim-gac-llr",)
        ),
        "codellama7b-closure-fim-4k": (
            CodeLlamaHFModels,
            ("/proj/berzelius-2023-175/users/x_andaf/training_logs/codellama7b-closure-fim-4k",)
        ),
        "codellama7b-databind-fim-llr-4k": (
            CodeLlamaHFModels,
            ("/proj/berzelius-2023-175/users/x_andaf/training_logs/codellama7b-databind-fim-llr-4k",)
        ),
        "codellama7b-ftf-5k": (
            CodeLlamaHFModels,
            ("/proj/berzelius-2023-175/users/x_andaf/training_logs/codellama7b-ftf-5k",)
        ),
        "codellama7b-closure-fim-lora": (
            CodeLlamaLoRAHFModels,
            ("/proj/berzelius-2023-175/users/x_andaf/training_logs/codellama7b-closure-fim-lora",)
        ),
        "codellama7b-closure-fim-lora-checkpoint": (
            CodeLlamaLoRAHFModels,
            ("/proj/berzelius-2023-175/users/x_andaf/training_logs/codellama7b-closure-fim-lora/checkpoint-802",)
        ),
        "codellama7b-closure-lora-mix": (
            CodeLlamaLoRAHFModels,
            ("/proj/berzelius-2023-175/users/x_andaf/training_logs/codellama7b-closure-fim-lora/checkpoint-802",)
        ),
        "repairllama-lora": (
            CodeLlamaLoRAHFModels,
            ("ASSERT-KTH/RepairLLaMA-Optimal-IOR",)
        ),
        "codellama7b-best": (
            CodeLlamaHFModels,
            ("/proj/berzelius-2023-175/users/x_andaf/training_logs/codellama7b-fft-best",)
        ),
        "codellama7b-best-llr": (
            CodeLlamaHFModels,
            ("/proj/berzelius-2023-175/users/x_andaf/training_logs/codellama7b-fft-best-llr",)
        )
    }

    @classmethod
    def get_generation(cls, name: str, **kwargs) -> PatchGenerationStrategy:
        if name.lower().strip() not in cls.__MODELS:
            raise ValueError(f"Unknown model {name}")
        model_class, model_args = cls.__MODELS[name.lower().strip()]
        return model_class(*model_args, **kwargs)
