from elleelleaime.generate.strategies.strategy import PatchGenerationStrategy
from dataclasses import dataclass
from transformers import LlamaForCausalLM, CodeLlamaTokenizer
from typing import Any

import torch
import threading
import logging


@dataclass
class GenerateSettings:
    name: str
    do_sample: bool = False
    temperature: float = 1.0
    num_beams: int = 1
    num_return_sequences: int = 10
    max_new_tokens: int = 512


class CodeLLaMAInfilling(PatchGenerationStrategy):
    __SUPPORTED_MODELS = {
        "meta-llama/CodeLlama-7b-hf",
        "meta-llama/CodeLlama-13b-hf",
        "meta-llama/CodeLlama-34b-hf",
        "meta-llama/CodeLlama-70b-hf",
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
        ), f"Model {model_name} not supported by {self.__class__.__name__}"
        self.model_name = model_name
        self.__load_model()
        # Generation settings
        assert (
            kwargs.get("generation_strategy", "beam_search")
            in self.__GENERATION_STRATEGIES
        ), f"Generation strategy {kwargs.get('generation_strategy', 'beam_search')} not supported by {self.__class__.__name__}"
        self.generate_settings = self.__GENERATION_STRATEGIES[
            kwargs.get("generation_strategy", "beam_search")
        ]
        self.generate_settings.max_new_tokens = kwargs.get(
            "max_new_tokens", GenerateSettings.max_new_tokens
        )
        self.generate_settings.num_return_sequences = kwargs.get(
            "num_return_sequences", GenerateSettings.num_return_sequences
        )
        self.generate_settings.num_beams = kwargs.get(
            "num_beams", GenerateSettings.num_beams
        )
        self.generate_settings.temperature = kwargs.get(
            "temperature", GenerateSettings.temperature
        )

    def __load_model(self):
        # Setup environment
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.context_size = 16384

        # Setup kwargs
        kwargs = dict(
            torch_dtype=torch.bfloat16,
        )

        # Load the model and tokenizer
        with self.__MODELS_LOCK:
            if self.__MODELS_LOADED:
                return
            self.__TOKENIZER = CodeLlamaTokenizer.from_pretrained(self.model_name)
            self.__MODEL = LlamaForCausalLM.from_pretrained(
                self.model_name, device_map="auto", **kwargs
            )
            self.__MODEL.eval()
            self.__MODELS_LOADED = True

    def _generate_impl(self, prompt: str) -> Any:
        if prompt.count("<FILL_ME>") > 1:
            logging.warning(
                "Prompt should contain exactly at most one <FILL_ME> tag, but it contains %d. Skipping bug.",
                prompt.count("<FILL_ME>"),
            )
            return None

        input_ids = self.__TOKENIZER(prompt, return_tensors="pt")["input_ids"].to(
            self.device
        )

        max_length = self.generate_settings.max_new_tokens + input_ids.shape[1]
        if max_length > self.context_size:
            logging.warning(
                "warning: max_length %s is greater than the context window %s"
                % (max_length, self.context_size)
            )
            return None

        with torch.no_grad():
            generated_ids = self.__MODEL.generate(
                input_ids,
                max_new_tokens=self.generate_settings.max_new_tokens,
                num_beams=self.generate_settings.num_beams,
                num_return_sequences=self.generate_settings.num_return_sequences,
                early_stopping=True,
                do_sample=self.generate_settings.do_sample,
                temperature=self.generate_settings.temperature,
            )

        input_len = input_ids.shape[1]
        fillings_ids = generated_ids[:, input_len:]
        fillings = self.__TOKENIZER.batch_decode(fillings_ids, skip_special_tokens=True)

        if "<FILL_ME>" in prompt:
            return [prompt.replace("<FILL_ME>", filling) for filling in fillings]
        else:
            return list(fillings)
