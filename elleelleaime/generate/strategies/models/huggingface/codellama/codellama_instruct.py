from elleelleaime.generate.strategies.strategy import PatchGenerationStrategy
from dataclasses import dataclass
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.tokenization_utils_base import PreTrainedTokenizerBase
from typing import Any, List

import tqdm
import torch
import threading


@dataclass
class GenerateSettings:
    name: str
    do_sample: bool = False
    temperature: float = 1.0
    num_beams: int = 1
    num_return_sequences: int = 10
    max_length: int = 4096
    early_stopping: bool = False


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
            early_stopping=True,
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
        # Generation settings
        assert (
            kwargs.get("generation_strategy", "sampling")
            in self.__GENERATION_STRATEGIES
        ), f"Generation strategy {kwargs.get('generation_strategy', 'samlping')} not supported by {self.__class__.__name__}"
        self.generate_settings = self.__GENERATION_STRATEGIES[
            kwargs.get("generation_strategy", "samlping")
        ]
        self.batch_size = kwargs.get("batch_size", 1)
        self.generate_settings.num_return_sequences = kwargs.get(
            "num_return_sequences", GenerateSettings.num_return_sequences
        )
        self.generate_settings.num_beams = kwargs.get(
            "num_beams", GenerateSettings.num_beams
        )
        self.generate_settings.temperature = kwargs.get(
            "temperature", GenerateSettings.temperature
        )
        self.__load_model(**kwargs)

    def __load_model(self, **kwargs):
        # Setup environment
        self.device = "cuda"
        self.context_size = self.generate_settings.max_length

        # Setup kwargs
        model_kwargs = dict(
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )

        # Load the model and tokenizer
        with self.__MODELS_LOCK:
            if self.__MODELS_LOADED:
                return

            # Load tokenizer
            self.__TOKENIZER: PreTrainedTokenizerBase = AutoTokenizer.from_pretrained(
                self.model_name
            )
            self.__TOKENIZER.pad_token = self.__TOKENIZER.eos_token
            self.__TOKENIZER.padding_side = "left"
            # Load model
            self.__MODEL = AutoModelForCausalLM.from_pretrained(
                self.model_name, **model_kwargs
            )
            # Load LoRA adapter
            if kwargs.get("adapter_name", None):
                self.__MODEL = AutoModelForCausalLM.from_pretrained(
                    self.model_name, **model_kwargs
                )
                self.__MODEL = PeftModel(self.__MODEL, kwargs["adapter_name"])
                self.__MODEL = self.__MODEL.merge_and_unload()
            self.__MODEL.eval()
            self.__MODELS_LOADED = True

    def __format_prompt(self, prompt: str) -> str:
        return f"<s>[INST] {prompt} [\\INST]"

    def __chunk_list(self, lst: List[str], n: int):
        for i in range(0, len(lst), n):
            yield lst[i : i + n]

    def _generate_impl(self, chunk: List[str]) -> Any:
        result = []
        batches = [chunk for chunk in self.__chunk_list(chunk, self.batch_size)]
        for batch in tqdm.tqdm(
            batches, desc="Generating patches...", total=len(batches)
        ):
            batch_result = self._generate_batch(batch)
            result.extend(batch_result)
        return result

    def _generate_batch(self, batch: List[str]) -> Any:
        formatted_prompts = [self.__format_prompt(p) for p in batch]

        inputs = self.__TOKENIZER(
            formatted_prompts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.context_size,
        )
        inputs = inputs.to(self.device)

        with torch.no_grad():
            generated_ids = self.__MODEL.generate(
                **inputs,
                max_length=self.generate_settings.max_length,
                num_beams=self.generate_settings.num_beams,
                num_return_sequences=self.generate_settings.num_return_sequences,
                early_stopping=self.generate_settings.early_stopping,
                do_sample=self.generate_settings.do_sample,
                temperature=self.generate_settings.temperature,
            )

        responses = self.__TOKENIZER.batch_decode(
            generated_ids, skip_special_tokens=True
        )
        responses = [
            r.split("[\\INST]")[1] if "[\\INST]" in r else None for r in responses
        ]

        return responses
