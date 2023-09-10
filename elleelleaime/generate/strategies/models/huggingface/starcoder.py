from elleelleaime.generate.strategies.strategy import PatchGenerationStrategy
from dataclasses import dataclass
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import Any

import torch
import threading
import logging


@dataclass
class GenerateSettings:
    name: str
    num_beams: int = 1
    do_sample: bool = False
    temperature: float = 0.0
    max_new_tokens: int = 128
    num_return_sequences: int = 10
    max_new_tokens: int = 1024


class StarCoderHFModels(PatchGenerationStrategy):
    __SUPPORTED_MODELS = {
        "bigcode/starcoderbase",
        "bigcode/starcoderplus",
    }

    __GENERATION_STRATEGIES = {
        "beam_search": GenerateSettings(
            name="beam_search",
        ),
        "sampling": GenerateSettings(
            name="sampling",
            do_sample=True,
        ),
    }

    __MODEL = None
    __TOKENIZER = None
    __MODELS_LOADED: bool = False
    __MODELS_LOCK: threading.Lock = threading.Lock()

    def __init__(self, model_name: str, **kwargs) -> None:
        assert (
            model_name in self.__SUPPORTED_MODELS
        ), f"Model {model_name} not supported by StarCoderHFModels"
        self.model_name = model_name
        self.__load_model()
        # Generation settings
        assert (
            kwargs.get("generation_strategy", "beam_search")
            in self.__GENERATION_STRATEGIES
        ), f"Generation strategy {kwargs.get('generation_strategy', 'beam_search')} not supported by StarCoderHFModels"
        self.generate_settings = self.__GENERATION_STRATEGIES[
            kwargs.get("generation_strategy", "beam_search")
        ]
        self.generate_settings.max_new_tokens = kwargs.get("max_new_tokens", 128)
        self.generate_settings.num_return_sequences = kwargs.get(
            "num_return_sequences", 10
        )
        self.generate_settings.num_beams = kwargs.get("num_beams", 1)
        self.generate_settings.temperature = kwargs.get("temperature", 0.2)

    def __load_model(self):
        # Setup environment
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.context_size = 8192

        # Setup kwargs
        kwargs = dict(
            torch_dtype=torch.bfloat16,
        )

        # Load the model and tokenizer
        with self.__MODELS_LOCK:
            if self.__MODELS_LOADED:
                return
            self.__TOKENIZER = AutoTokenizer.from_pretrained(self.model_name)
            self.__MODEL = AutoModelForCausalLM.from_pretrained(
                self.model_name, device_map="auto", **kwargs
            )
            self.__MODELS_LOADED = True

    def _generate_impl(self, prompt: str) -> Any:
        inputs = self.__TOKENIZER.encode(prompt, return_tensors="pt").to(device)

        max_length = self.generate_settings.max_new_tokens + input.input_ids.shape[1]
        if max_length > self.context_size:
            logging.warning(
                "warning: max_length %s is greater than the context window %s"
                % (max_length, self.context_size)
            )
            return None

        with torch.no_grad():
            generated_ids = self.__MODEL.generate(
                inputs,
                max_new_tokens=self.generate_settings.max_new_tokens,
                num_beams=self.generate_settings.num_beams,
                num_return_sequences=self.generate_settings.num_return_sequences,
                early_stopping=True,
                do_sample=self.generate_settings.do_sample,
                temperature=self.generate_settings.temperature,
            )

        input_len = input.input_ids.shape[1]
        fillings_ids = generated_ids[:, input_len:]
        fillings = self.__TOKENIZER.batch_decode(fillings_ids, skip_special_tokens=True)

        # Reorganize the function with the fillings
        # The prompt is organized as follows:
        # <fim_prefix><prefix><fim_suffix><suffix><fim_middle>
        # We want to achieve
        # <prefix><middle><suffix>
        # where <middle> is the the filling
        def get_prefix(text):
            return text.split("<fim_prefix>")[1].split("<fim_suffix>")[0]

        def get_suffix(text):
            return text.split("<fim_suffix>")[1].split("<fim_middle>")[0]

        def get_middle(text):
            return text.split("<fim_middle>")[1]

        fillings = [
            get_prefix(filling) + get_middle(filling) + get_suffix(filling)
            for filling in fillings
        ]

        print(fillings[0])

        return fillings
