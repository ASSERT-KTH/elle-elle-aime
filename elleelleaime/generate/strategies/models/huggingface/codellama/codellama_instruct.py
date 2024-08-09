from elleelleaime.generate.strategies.strategy import PatchGenerationStrategy
from dataclasses import dataclass
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
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
    max_new_tokens: int = 4096


class CodeLLaMAIntruct(PatchGenerationStrategy):
    __SUPPORTED_MODELS = {
        "meta-llama/CodeLlama-7b-Instruct-hf",
        "meta-llama/CodeLlama-13b-Instruct-hf",
        "meta-llama/CodeLlama-34b-Instruct-hf",
        "meta-llama/CodeLlama-70b-Instruct-hf",
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
        self.__load_model(**kwargs)
        # Generation settings
        assert (
            kwargs.get("generation_strategy", "sampling")
            in self.__GENERATION_STRATEGIES
        ), f"Generation strategy {kwargs.get('generation_strategy', 'samlping')} not supported by {self.__class__.__name__}"
        self.generate_settings = self.__GENERATION_STRATEGIES[
            kwargs.get("generation_strategy", "samlping")
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

    def __load_model(self, **kwargs):
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

            # Load tokenizer
            self.__TOKENIZER = AutoTokenizer.from_pretrained(self.model_name)
            self.__TOKENIZER.pad_token = self.__TOKENIZER.eos_token
            # Load model
            self.__MODEL = AutoModelForCausalLM.from_pretrained(
                self.model_name, device_map="auto", **kwargs
            )
            # Load LoRA adapter (if requested)
            if kwargs.get("adapter_name", None) is not None:
                self.__MODEL = PeftModel.from_pretrained(
                    self.__MODEL, kwargs.get("adapter_name")
                )
                self.__MODEL.merge_and_unload()
            self.__MODEL.eval()
            self.__MODELS_LOADED = True

    def __format_prompt(self, prompt: str) -> str:
        return f"<s>[INST] {prompt} [\\INST]"

    def _generate_impl(self, prompt: str) -> Any:
        formatted_prompt = self.__format_prompt(prompt)

        input_ids = self.__TOKENIZER(formatted_prompt, return_tensors="pt")["input_ids"]
        input_ids = input_ids.to(self.device)

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

        return list(fillings)
