from abc import ABC, abstractmethod

from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.test_result import TestResult
from elleelleaime.core.benchmarks.compile_result import CompileResult

class Bug(ABC):
    """
    The abstract class for representing a bug.
    """

    def __init__(self, benchmark: Benchmark, identifier: str) -> None:
        self.benchmark = benchmark
        self.identifier = identifier

    def get_identifier(self) -> str:
        return self.identifier

    @abstractmethod
    def checkout(self, path: str, fixed: bool = False) -> bool:
        pass

    @abstractmethod
    def apply_diff(self, path:str) -> bool:
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