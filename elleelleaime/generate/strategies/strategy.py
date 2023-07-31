from abc import ABC, abstractmethod

from typing import Any, final


class PatchGenerationStrategy(ABC):
    @abstractmethod
    def _generate_impl(self, prompt: str) -> Any:
        """
        Implemenation method for the generation strategy.
        """
        pass

    @final
    def _handle_none_prompt(self) -> Any:
        """
        Handles the case where the prompt is None. For now, we simply return None.
        """
        return None

    @final
    def generate(self, prompt: str) -> Any:
        """
        Returns the generation results for the given prompt.

        :param prompt: The prompt to use for generation.
        :return: A tuple containing the generation results.
        """
        # Implements the logic common to all generation strategies
        if prompt is None:
            return self._handle_none_prompt()

        return self._generate_impl(prompt)
