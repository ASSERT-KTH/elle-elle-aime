from elleelleaime.generate.strategies.strategy import PatchGenerationStrategy

from dotenv import load_dotenv
from typing import Any, List

import os
import openai
import backoff


class NvidiaModels(PatchGenerationStrategy):
    def __init__(self, model_name: str, **kwargs) -> None:
        self.model_name = model_name
        self.temperature = kwargs.get("temperature", 0.0)
        self.n_samples = kwargs.get("n_samples", 1)

        load_dotenv()
        openai.api_key = os.getenv("NVIDIA_API_KEY")
        self.client = openai.OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=openai.api_key,
        )

    @backoff.on_exception(backoff.expo, openai.RateLimitError)
    def _completions_with_backoff(self, **kwargs):
        return self.client.chat.completions.create(**kwargs)

    def _generate_impl(self, chunk: List[str]) -> Any:
        result = []

        for prompt in chunk:
            completion = self._completions_with_backoff(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                n=self.n_samples,
            )
            result.append(completion.to_dict())

        return result
