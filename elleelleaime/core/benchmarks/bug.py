from abc import ABC, abstractmethod
from unidiff import PatchSet
import os

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

    def get_buggy_file_path(self, work_dir: str) -> str:
        diff = PatchSet(self.get_ground_truth())

        if self.is_ground_truth_inverted():
            return os.path.join(
                work_dir,
                diff[0].target_file[2:]
                if diff[0].target_file.startswith("b/")
                else diff[0].target_file,
            )
        else:
            return os.path.join(
                work_dir,
                diff[0].source_file[2:]
                if diff[0].source_file.startswith("a/")
                else diff[0].source_file,
            )

    def get_fixed_file_path(self, work_dir: str) -> str:
        diff = PatchSet(self.get_ground_truth())

        if self.is_ground_truth_inverted():
            return os.path.join(
                work_dir,
                diff[0].source_file[2:]
                if diff[0].source_file.startswith("a/")
                else diff[0].source_file,
            )
        else:
            return os.path.join(
                work_dir,
                diff[0].target_file[2:]
                if diff[0].target_file.startswith("b/")
                else diff[0].target_file,
            )

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
