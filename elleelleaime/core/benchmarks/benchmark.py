from abc import ABC, abstractmethod

# prevent circular import
class Benchmark(ABC):
    pass

import pathlib

from typing import Set
from core.benchmarks.bug import Bug

class Benchmark(ABC):
    """
    The abstract class for representing a benchmark.
    """

    def __init__(self, identifier: str, path: pathlib.Path) -> None:
        self.identifier = identifier
        self.path = path.absolute()
        self.bugs = set()

    def get_identifier(self) -> str:
        return self.identifier

    def get_path(self) -> pathlib.Path:
        return self.path
    
    @abstractmethod
    def get_bin(self) -> pathlib.Path:
        pass

    def get_bugs(self) -> Set[Bug]:
        return self.bugs

    def add_bug(self, bug: Bug) -> None:
        self.bugs.add(bug)

    @abstractmethod
    def initialize(self) -> None:
        pass