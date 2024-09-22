from typing import Optional
from .cost_strategy import CostStrategy

import tqdm
import logging


class OpenRouterCostStrategy(CostStrategy):

    __COST_PER_MILLION_TOKENS = {
        "meta-llama:llama-3.1-405b-instruct": {
            "prompt": 2.8,
            "completion": 2.8,
        },
        "deepseek-v2.5": {
            "prompt": 2,
            "completion": 2,
        },
        "mistral-large-2407": {
            "prompt": 2,
            "completion": 6,
        },
    }

    @staticmethod
    def compute_costs(samples: list, model_name: str) -> Optional[dict]:
        if model_name not in OpenRouterCostStrategy.__COST_PER_MILLION_TOKENS:
            return None

        costs = {
            "prompt_cost": 0.0,
            "completion_cost": 0.0,
            "total_cost": 0.0,
        }

        for sample in tqdm.tqdm(samples, f"Computing costs for {model_name}..."):
            if sample["generation"]:
                if not isinstance(sample["generation"], list):
                    generation = [sample["generation"]]
                else:
                    generation = sample["generation"]
                for g in generation:
                    if "usage" not in g:
                        logging.warning(f"'usage' key not found in {g}")
                        continue
                    prompt_token_count = g["usage"]["prompt_tokens"]
                    candidates_token_count = g["usage"]["completion_tokens"]

                    prompt_cost = OpenRouterCostStrategy.__COST_PER_MILLION_TOKENS[
                        model_name
                    ]["prompt"]
                    completion_cost = OpenRouterCostStrategy.__COST_PER_MILLION_TOKENS[
                        model_name
                    ]["completion"]

                    costs["prompt_cost"] += prompt_cost * prompt_token_count / 1000000
                    costs["completion_cost"] += (
                        completion_cost * candidates_token_count / 1000000
                    )

        costs["total_cost"] = costs["prompt_cost"] + costs["completion_cost"]
        return costs
