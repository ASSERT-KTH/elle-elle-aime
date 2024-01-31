from elleelleaime.generate.strategies.strategy import PatchGenerationStrategy
from dataclasses import dataclass
from accelerate import dispatch_model
from transformers import LlamaForCausalLM, CodeLlamaTokenizer
from peft import PeftModel
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    BitsAndBytesConfig,
)
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
    max_new_tokens: int = 256
    num_return_sequences: int = 10


class CodeLlamaLoRAHFModels(PatchGenerationStrategy):
    __SUPPORTED_MODELS = {
        # TODO: make this a regex
        "/proj/berzelius-2023-175/users/x_andaf/training_logs/codellama7b-closure-fim-lora",
        "/proj/berzelius-2023-175/users/x_andaf/training_logs/codellama7b-closure-fim-lora/checkpoint-802",
        "ASSERT-KTH/RepairLLaMA-Optimal-IOR",
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
        ), f"Model {model_name} not supported by CodeLlamaHFModels"
        self.model_name = model_name
        self.__load_model()
        # Generation settings
        assert (
            kwargs.get("generation_strategy", "beam_search")
            in self.__GENERATION_STRATEGIES
        ), f"Generation strategy {kwargs.get('generation_strategy', 'beam_search')} not supported by CodeLlamaHFModels"
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
        self.context_size = 2048

        # Setup kwargs
        kwargs = dict(
            torch_dtype=torch.float16,
            load_in_8bit=True,
            trust_remote_code=True,
            quantization_config=BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=6.0
            ),
        )

        # Load the model and tokenizer
        with self.__MODELS_LOCK:
            if self.__MODELS_LOADED:
                return
            self.__TOKENIZER = AutoTokenizer.from_pretrained(self.model_name)
            self.__TOKENIZER.pad_token = self.__TOKENIZER.eos_token
            self.__TOKENIZER.pad_token_id = self.__TOKENIZER.pad_token_id
            model = AutoModelForCausalLM.from_pretrained(
                "codellama/CodeLlama-7b-hf",
                device_map=None,
                **kwargs
            )
            self.__MODEL = PeftModel.from_pretrained(
                model,
                self.model_name,
                torch_dtype=torch.float16,
                adapter_name="project",
            )
            # self.__MODEL.load_adapter("ASSERT-KTH/RepairLLaMA-Optimal-IOR", adapter_name="task")
            if not hasattr(self.__MODEL, "hf_device_map"):
                self.__MODEL.cuda()
            # self.__MODEL.add_weighted_adapter(["task","project"], [1.0, 1.0], "repair", combination_type="cat")
            # self.__MODEL.set_adapter("repair")
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
            try:
                generated_ids = self.__MODEL.generate(
                    input_ids=input_ids,
                    max_new_tokens=self.generate_settings.max_new_tokens,
                    num_beams=self.generate_settings.num_beams,
                    num_return_sequences=self.generate_settings.num_return_sequences,
                    early_stopping=True,
                    do_sample=self.generate_settings.do_sample,
                    temperature=self.generate_settings.temperature,
                )
            except torch.cuda.OutOfMemoryError:
                return None

        input_len = input_ids.shape[1]
        fillings_ids = generated_ids[:, input_len:]
        fillings = self.__TOKENIZER.batch_decode(fillings_ids, skip_special_tokens=True)

        # Remove eos_token
        fillings = [filling.replace("</s>", "") for filling in fillings]

        if "<FILL_ME>" in prompt:
            return [prompt.replace("<FILL_ME>", filling) for filling in fillings]
        else:
            return list(fillings)
