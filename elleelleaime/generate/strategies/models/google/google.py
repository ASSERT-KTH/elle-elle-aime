from elleelleaime.generate.strategies.strategy import PatchGenerationStrategy

from dotenv import load_dotenv
from typing import Any, List

import os
import google.generativeai as genai


class GoogleModels(PatchGenerationStrategy):
    def __init__(self, model_name: str, **kwargs) -> None:
        self.model_name = model_name
        self.temperature = kwargs.get("temperature", 0.0)
        self.n_samples = kwargs.get("n_samples", 1)

        load_dotenv()
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    def __get_config(self):
        return genai.types.GenerationConfig(
            temperature=self.temperature,
        )

    def _generate_impl(self, chunk: List[str]) -> Any:
        result = []

        model = genai.GenerativeModel(self.model_name)

        for prompt in chunk:
            p_results = []
            for _ in range(self.n_samples):
                completion = model.generate_content(
                    prompt, generation_config=self.__get_config()
                )
                p_results.append(completion.to_dict())
            result.append(p_results)

        return result
