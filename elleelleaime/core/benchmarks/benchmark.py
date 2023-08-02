from abc import ABC, abstractmethod


# prevent circular import
# Benchmark imports Bug -> Bug imports Benchmark -> Benchmark imports Bug -> ...
class Benchmark(ABC):
    pass


import pathlib

from typing import Dict, Optional
from elleelleaime.core.benchmarks.bug import Bug


class Benchmark(ABC):
    """
    The abstract class for representing a benchmark.
    """

    def __init__(self, identifier: str, path: pathlib.Path) -> None:
        self.identifier: str = identifier
        self.path: pathlib.Path = path.absolute()
        self.bugs: Dict[str, Bug] = dict()

    def get_identifier(self) -> str:
        return self.identifier

    def get_path(self) -> pathlib.Path:
        return self.path

    @abstractmethod
    def get_bin(self) -> pathlib.Path:
        pass

    def get_bugs(self) -> Dict[str, Bug]:
        return self.bugs

    def get_bug(self, identifier) -> Optional[Bug]:
        return self.bugs[identifier]

    def add_bug(self, bug: Bug) -> None:
        assert bug.get_identifier() not in self.bugs
        self.bugs[bug.get_identifier()] = bug

    @abstractmethod
    def initialize(self) -> None:
        pass
