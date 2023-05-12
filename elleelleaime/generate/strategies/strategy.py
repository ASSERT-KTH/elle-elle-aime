from abc import ABC, abstractmethod

from typing import Any

class PatchGenerationStrategy(ABC):

    @abstractmethod
    def generate(self, prompt: str) -> Any:
        """
        Returns the generation results for the given prompt.

        :param prompt: The prompt to use for generation.
        :return: A tuple containing the generation results.
        """
        pass