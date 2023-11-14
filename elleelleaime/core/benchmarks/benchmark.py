from abc import ABC, abstractmethod


# prevent circular import
# Benchmark imports Bug -> Bug imports Benchmark -> Benchmark imports Bug -> ...
class Benchmark(ABC):
    pass


import pathlib

from typing import Dict, Set, Optional
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

    def get_bin(self) -> Optional[pathlib.Path]:
        return None

    def get_bugs(self) -> Set[Bug]:
        return set(self.bugs.values())

    def get_bug(self, identifier) -> Optional[Bug]:
        return self.bugs[identifier]

    def add_bug(self, bug: Bug) -> None:
        assert bug.get_identifier() not in self.bugs
        self.bugs[bug.get_identifier()] = bug

    def get_oldest_bug(self, project: Optional[str] = None) -> Dict[str, Bug]:
        raise NotImplementedError(
            f"get_oldest_bug is not implemented for {self.identifier}"
        )

    @abstractmethod
    def initialize(self) -> None:
        pass
