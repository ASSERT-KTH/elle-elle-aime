from .strategy import MufinStrategy
from .strategies.breaker import BreakerStrategy


class MufinStrategyRegistry:
    """
    Class for storing and retrieving sampling strategies for MUFIN.
    """

    __STRATEGIES: dict[str, type] = {
        "mufin-breaker": BreakerStrategy,
    }

    @classmethod
    def get_strategy(cls, name: str, **kwargs) -> MufinStrategy:
        if name.lower().strip() not in cls.__STRATEGIES:
            raise ValueError(f"Unknown sampling strategy {name}")
        return cls.__STRATEGIES[name.lower().strip()](**kwargs)
