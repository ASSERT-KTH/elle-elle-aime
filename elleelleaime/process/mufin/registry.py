from .strategy import MufinProcessStrategy
from .strategies.mufin import MufinStrategy


class MufinStrategyRegistry:
    """
    Class for storing and retrieving sampling strategies for MUFIN.
    """

    __STRATEGIES: dict[str, type] = {
        "mufin": MufinStrategy,
    }

    @classmethod
    def get_strategy(cls, name: str, **kwargs) -> MufinProcessStrategy:
        if name.lower().strip() not in cls.__STRATEGIES:
            raise ValueError(f"Unknown sampling strategy {name}")
        return cls.__STRATEGIES[name.lower().strip()](**kwargs)
