import requests.exceptions
from elleelleaime.generate.strategies.strategy import PatchGenerationStrategy

from dotenv import load_dotenv
from typing import Any, List

import os
import requests
import json
import backoff


class OpenRouterModels(PatchGenerationStrategy):
    def __init__(self, model_name: str, **kwargs) -> None:
        self.model_name = model_name
        self.temperature = kwargs.get("temperature", 0.0)
        self.n_samples = kwargs.get("n_samples", 1)
        self.provider = kwargs.get("provider", None)
        self.provider_args = {
            "require_parameters": True,
            "allow_fallbacks": False,
        }
        if self.provider:
            self.provider_args["order"] = [self.provider]

        load_dotenv()
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.RequestException, json.JSONDecodeError, Exception),
        max_tries=5,
        raise_on_giveup=False,
    )
    def _completions_with_backoff(self, **kwargs):
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.openrouter_api_key}",
                # For including your app on openrouter.ai rankings.
                "HTTP-Referer": f"https://repairbench.github.io/",
                # Shows in rankings on openrouter.ai.
                "X-Title": f"RepairBench",
            },
            data=json.dumps(kwargs),
        )

        response = response.json()

        if "error" in response:
            raise Exception(response["error"])

        return response

    def _generate_impl(self, chunk: List[str]) -> Any:
        result = []

        for prompt in chunk:
            result_sample = []
            for _ in range(self.n_samples):
                completion = self._completions_with_backoff(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    provider=self.provider_args,
                )
                result_sample.append(completion)
            result.append(result_sample)

        return result
