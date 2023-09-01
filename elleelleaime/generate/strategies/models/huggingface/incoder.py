from elleelleaime.generate.strategies.strategy import PatchGenerationStrategy
from typing import Any

import torch
import re
import threading
from dataclasses import dataclass
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import Optional


@dataclass
class GenerateSettings:
    name: str
    num_beams: int = 1
    do_sample: bool = False
    temperature: float = 0.0
    max_new_tokens: int = 128
    num_return_sequences: int = 10


class IncoderHFModels(PatchGenerationStrategy):
    __SUPPORTED_MODELS = {
        "facebook/incoder-6B",
        "facebook/incoder-1B",
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
        ), f"Model {model_name} not supported by IncoderModels"
        self.model_name = model_name
        self.__load_model()
        # Generation settings
        assert (
            kwargs.get("generation_strategy", "beam_search")
            in self.__GENERATION_STRATEGIES
        ), f"Generation strategy {kwargs.get('generation_strategy', 'beam_search')} not supported by IncoderHFModels"
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
        if self.model_name == "facebook/incoder-6B":
            kwargs = dict(
                revision="float16",
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True,
            )
        else:
            kwargs = dict()

        # Load the model and tokenizer
        with self.__MODELS_LOCK:
            if self.__MODELS_LOADED:
                return
            self.__TOKENIZER = AutoTokenizer.from_pretrained(self.model_name)
            self.__MODEL = AutoModelForCausalLM.from_pretrained(
                self.model_name, device_map="auto", **kwargs
            )
            if self.device == "cuda":
                self.__MODEL = self.__MODEL.half()

            self.__MODELS_LOADED = True

    def _generate_impl(self, prompt: str) -> Any:
        # Setup generation settings
        predicted_texts = []
        # signals the start of a document
        BOS = "<|endoftext|>"
        # signals the end of a generated infill
        EOM = "<|endofmask|>"

        def generate(
            input: str, generate_settings: GenerateSettings
        ) -> Optional[list[str]]:
            """
            Do standard left-to-right completion of the prefix `input` by sampling from the model
            """
            input_ids = self.__TOKENIZER(input, return_tensors="pt").input_ids
            input_ids = input_ids.to(self.device)
            max_length = generate_settings.max_new_tokens + input_ids.flatten().size(0)
            if max_length > self.context_size:
                print(
                    "warning: max_length %s is greater than the context window %s"
                    % (max_length, self.context_size)
                )
                return None
            with torch.no_grad():
                outputs = self.__MODEL.generate(
                    input_ids,
                    max_length=max_length,
                    num_beams=generate_settings.num_beams,
                    num_return_sequences=generate_settings.num_return_sequences,
                    early_stopping=True,
                    do_sample=generate_settings.do_sample,
                    temperature=generate_settings.temperature,
                )
            # pass clean_up_tokenization_spaces=False to avoid removing spaces before punctuation, e.g. "from ." -> "from."
            detok_hypo_strs = self.__TOKENIZER.batch_decode(
                outputs, clean_up_tokenization_spaces=False
            )
            detok_hypo_strs = [
                detok_hypo_str[len(BOS) :]
                if detok_hypo_str.startswith(BOS)
                else detok_hypo_str
                for detok_hypo_str in detok_hypo_strs
            ]
            for output in detok_hypo_strs:
                print(output)
            return detok_hypo_strs

        def infill(
            prompt: str, generate_settings: GenerateSettings
        ) -> Optional[list[str]]:
            """
            Generate infills to complete a partial document, e.g.
            [A C E] -> [A B C D E], where B and D are infills that have been generated.
            """
            completions: list[list[str]] = [
                [] for _ in range(generate_settings.num_return_sequences)
            ]

            # Split prompt into parts separated by sentinels
            # We identify the sentinels with a regex pattern r"<\|mask:\d\|>"
            # We do not include the last sentinel as it is not followed by any text
            parts = re.split(r"<\|mask:\d\|>", prompt)[:-1]

            for sentinel_ix, part in enumerate(parts[:-1]):
                completions = [
                    [] + [part] for _ in range(generate_settings.num_return_sequences)
                ]
                prompt += "<|mask:%d|>" % sentinel_ix
                # TODO: this is inefficient as it requires re-encoding prefixes repeatedly
                generations = generate(prompt, generate_settings)
                # TODO: save error value
                if generations is None:
                    return None

                for i, generation in enumerate(generations):
                    completion = generation[len(prompt) :]
                    if EOM not in completion:
                        completion += EOM
                    completion = completion[: completion.index(EOM) + len(EOM)]
                    infilled = completion[: -len(EOM)]
                    completions[i].append(infilled)

                    # TODO: maybe keep all 10 a generate beam starting on those 10?
                    if i == 1:
                        prompt += completion

            completions = [x + [parts[-1]] for x in completions]
            return ["".join(completion) for completion in completions]

        predicted_texts = infill(prompt, self.generate_settings)

        return predicted_texts
