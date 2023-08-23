from generate.strategies.strategy import PatchGenerationStrategy
from typing import Any


import json
import torch
import re
from dataclasses import dataclass
from transformers import AutoTokenizer, AutoModelForCausalLM


@dataclass
class GenerateSettings:
    name: str
    num_beams: int = 1
    do_sample: bool = False
    top_k: int = 0
    top_p: float = 1.0
    temperature: float = 0.0
    max_new_tokens: int = 128
    num_return_sequences: int = 1


class IncoderModels(PatchGenerationStrategy):
    __SUPPORTED_MODELS = {
        "facebook/incoder-6B",
        "facebook/incoder-1B",
    }

    __GENERATION_STRATEGIES = {
        "beam_search": GenerateSettings(
            name="beam_search",
            num_beams=10,
        ),
        "temperature_sampling": GenerateSettings(
            name="temperature_sampling",
            do_sample=True,
            temperature=0.2,
        ),
    }

    def __init__(self, model: str, **kwargs) -> None:
        assert (
            model in self.__SUPPORTED_MODELS
        ), f"Model {model} not supported by IncoderModels"
        self.model = model
        # Generation settings
        self.max_new_tokens = kwargs.get("max_new_tokens", 512)
        self.num_return_sequences = kwargs.get("num_return_sequences", 10)
        self.temperature = kwargs.get("temperature", 0.0)

    def _generate_impl(self, prompt: str) -> Any:
        # Setup environment
        device = "cuda" if torch.cuda.is_available() else "cpu"

        # Setup kwargs
        if "{model}" == "facebook/incoder-6B":
            context_size = 4096
            kwargs = dict(
                revision="float16",
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True,
            )
        else:
            context_size = 2048
            kwargs = dict(
                low_cpu_mem_usage=True,
            )

        # Load the model and tokenizer
        tokenizer = AutoTokenizer.from_pretrained("{model}")
        model = AutoModelForCausalLM.from_pretrained("{model}", **kwargs).to(device)
        if device == "cuda":
            model = model.half().cuda()

        # Setup generation settings
        # TODO: make this an option
        generate_settings = self.__GENERATION_STRATEGIES["beam_search"]
        predicted_texts = []
        # signals the start of a document
        BOS = "<|endoftext|>"
        # signals the end of a generated infill
        EOM = "<|endofmask|>"

        def generate(input: str, generate_settings: GenerateSettings):
            """
            Do standard left-to-right completion of the prefix `input` by sampling from the model
            """
            input_ids = tokenizer(input, return_tensors="pt").input_ids
            input_ids = input_ids.to(device)
            max_length = generate_settings.max_new_tokens + input_ids.flatten().size(0)
            if max_length > context_size:
                print(
                    "warning: max_length %s is greater than the context window %s"
                    % (max_length, context_size)
                )
                return None
            with torch.no_grad():
                output = model.generate(
                    input_ids=input_ids,
                    do_sample=generate_settings.do_sample,
                    num_beams=generate_settings.num_beams,
                    top_k=generate_settings.top_k,
                    top_p=generate_settings.top_p,
                    temperature=generate_settings.temperature,
                    max_length=max_length,
                )
            # pass clean_up_tokenization_spaces=False to avoid removing spaces before punctuation, e.g. "from ." -> "from."
            detok_hypo_str = tokenizer.decode(
                output.flatten(), clean_up_tokenization_spaces=False
            )
            if detok_hypo_str.startswith(BOS):
                detok_hypo_str = detok_hypo_str[len(BOS) :]
            return detok_hypo_str

        def infill(prompt: str, generate_settings: GenerateSettings):
            """
            Generate infills to complete a partial document, e.g.
            [A C E] -> [A B C D E], where B and D are infills that have been generated.
            """
            infills = []
            complete = []

            # Split prompt into parts separated by sentinels
            # We identify the sentinels with a regex pattern r"<\|mask:\d\|>"
            # We do not include the last sentinel as it is not followed by any text
            parts = re.split(r"<\|mask:\d\|>", prompt)[:-1]

            for sentinel_ix, part in enumerate(parts[:-1]):
                complete.append(part)
                prompt += "<|mask:%d|>" % sentinel_ix
                # TODO: this is inefficient as it requires re-encoding prefixes repeatedly
                completion = generate(prompt, generate_settings)
                if completion is None:
                    return None
                completion = completion[len(prompt) :]
                if EOM not in completion:
                    completion += EOM
                completion = completion[: completion.index(EOM) + len(EOM)]
                infilled = completion[: -len(EOM)]
                infills.append(infilled)
                complete.append(infilled)
                prompt += completion
            complete.append(parts[-1])
            text = "".join(complete)

            return text

        while len(predicted_texts) < generate_settings.num_return_sequences:
            predicted_texts.append(infill(prompt, generate_settings))

        return predicted_texts
