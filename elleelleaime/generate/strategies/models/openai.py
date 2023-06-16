from generate.strategies.strategy import PatchGenerationStrategy
from dotenv import load_dotenv
from typing import Any

import os
import openai
import openai.error
import backoff

class OpenAIChatCompletionModels(PatchGenerationStrategy):
    
    def __init__(self, model: str) -> None:
        self.model = model
        load_dotenv()
        openai.organization = os.getenv("OPENAI_ORG")
        openai.api_key = os.getenv("OPENAI_API_KEY")

    
    @staticmethod
    @backoff.on_exception(backoff.expo, openai.error.RateLimitError)
    def _completions_with_backoff(**kwargs):
        return openai.ChatCompletion.create(**kwargs)


    def _generate_impl(self, prompt: str) -> Any:
        # FIXME: get parameters from cli
        completion = self._completions_with_backoff(
            model = self.model,
            messages = [{"role": "user", "content": prompt}],
            temperature = 0.0,
        )
        return completion