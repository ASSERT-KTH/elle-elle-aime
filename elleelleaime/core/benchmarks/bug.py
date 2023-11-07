from abc import ABC, abstractmethod

from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.test_result import TestResult
from elleelleaime.core.benchmarks.compile_result import CompileResult


class Bug(ABC):
    """
    The abstract class for representing a bug.
    """

    def __init__(
        self, benchmark: Benchmark, identifier: str, ground_truth: str
    ) -> None:
        self.benchmark = benchmark
        self.identifier = identifier
        self.ground_truth = ground_truth

    def get_identifier(self) -> str:
        return self.identifier

    def get_ground_truth(self) -> str:
        return self.ground_truth

    def is_ground_truth_inverted(self) -> bool:
        return False

    @abstractmethod
    def checkout(self, path: str, fixed: bool = False) -> bool:
        pass

    @abstractmethod
    def cleanup(self, path: str) -> bool:
        pass

    @abstractmethod
    def apply_diff(self, path: str) -> bool:
        pass

    @abstractmethod
    def compile(self, path: str) -> CompileResult:
        pass

    @abstractmethod
    def test(self, path: str) -> TestResult:
        pass

    def __eq__(self, other) -> bool:
        if other == None:
            return False
        return self.identifier == other.identifier

    def __hash__(self) -> int:
        return hash(self.identifier)

    def __repr__(self) -> str:
        return self.get_identifier()
