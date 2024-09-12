from typing import Optional
from .cost_strategy import CostStrategy

import tqdm


class GoogleCostStrategy(CostStrategy):

    __COST_PER_MILLION_TOKENS = {
        "gemini-1.5-pro": {
            "prompt": 3.50,
            "completion": 10.50,
        }
    }

    __COST_PER_MILLION_TOKENS_OVER_128K = {
        "gemini-1.5-pro": {
            "prompt": 7.00,
            "completion": 21.00,
        }
    }

    @staticmethod
    def compute_costs(samples: list, model_name: str) -> Optional[dict]:
        if model_name not in GoogleCostStrategy.__COST_PER_MILLION_TOKENS:
            return None

        costs = {
            "prompt_cost": 0.0,
            "completion_cost": 0.0,
            "total_cost": 0.0,
        }

        for sample in tqdm.tqdm(samples, f"Computing costs for {model_name}..."):
            if sample["generation"]:
                for generation in sample["generation"]:
                    if "usage_metadata" not in generation:
                        continue

                    prompt_token_count = generation["usage_metadata"][
                        "prompt_token_count"
                    ]
                    candidates_token_count = generation["usage_metadata"][
                        "candidates_token_count"
                    ]
                    if prompt_token_count > 128000:
                        prompt_cost = (
                            GoogleCostStrategy.__COST_PER_MILLION_TOKENS_OVER_128K[
                                model_name
                            ]["prompt"]
                        )
                        completion_cost = (
                            GoogleCostStrategy.__COST_PER_MILLION_TOKENS_OVER_128K[
                                model_name
                            ]["completion"]
                        )
                    else:
                        prompt_cost = GoogleCostStrategy.__COST_PER_MILLION_TOKENS[
                            model_name
                        ]["prompt"]
                        completion_cost = GoogleCostStrategy.__COST_PER_MILLION_TOKENS[
                            model_name
                        ]["completion"]

                    costs["prompt_cost"] += prompt_cost * prompt_token_count / 1000000
                    costs["completion_cost"] += (
                        completion_cost * candidates_token_count / 1000000
                    )

        costs["total_cost"] = costs["prompt_cost"] + costs["completion_cost"]
        return costs
