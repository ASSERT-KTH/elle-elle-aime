from typing import Optional
from .cost_strategy import CostStrategy

import tqdm


class OpenAICostStrategy(CostStrategy):

    __COST_PER_THOUSAND_TOKENS = {
        "gpt-4o-2024-08-06": {
            "prompt": 0.00250,
            "completion": 0.01000,
        }
    }

    @staticmethod
    def compute_costs(samples: list, model_name: str) -> Optional[dict]:
        if model_name not in OpenAICostStrategy.__COST_PER_THOUSAND_TOKENS:
            return None

        costs = {
            "prompt_cost": 0.0,
            "completion_cost": 0.0,
            "total_cost": 0.0,
        }

        for sample in tqdm.tqdm(samples, f"Computing costs for {model_name}..."):
            if sample["generation"]:
                prompt_token_count = sample["generation"]["usage"]["prompt_tokens"]
                candidates_token_count = sample["generation"]["usage"][
                    "completion_tokens"
                ]

                prompt_cost = OpenAICostStrategy.__COST_PER_THOUSAND_TOKENS[model_name][
                    "prompt"
                ]
                completion_cost = OpenAICostStrategy.__COST_PER_THOUSAND_TOKENS[
                    model_name
                ]["completion"]

                costs["prompt_cost"] += prompt_cost * prompt_token_count / 1000
                costs["completion_cost"] += (
                    completion_cost * candidates_token_count / 1000
                )

        costs["total_cost"] = costs["prompt_cost"] + costs["completion_cost"]
        return costs
