import subprocess
import backoff
import shutil
import re
import os
from elleelleaime.core.benchmarks.benchmark import Benchmark

from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.benchmarks.test_result import TestResult
from elleelleaime.core.benchmarks.compile_result import CompileResult


class GitBugJavaBug(Bug):
    """
    The class for representing GitBug-Java bugs
    """

    def __init__(self, benchmark: Benchmark, bid: str, ground_truth: str) -> None:
        super().__init__(benchmark, bid, ground_truth, False)

    def checkout(self, path: str, fixed: bool = False) -> bool:
        # Remove the directory if it exists
        shutil.rmtree(path, ignore_errors=True)

        # Checkout the bug
        checkout_run = self.benchmark.run_command(
            f"checkout {self.identifier} {path} {'--fixed' if fixed else ''}"
        )

        return checkout_run.returncode == 0

    def compile(self, path: str) -> CompileResult:
        return CompileResult(None)

    def test(self, path: str) -> TestResult:
        try:
            run = self.benchmark.run_command(
                f"run {path}", check=False, timeout=30 * 60
            )

            m = re.search(r"Failing tests: ([0-9]+)", run.stdout.decode("utf-8"))
            return TestResult(
                run.returncode == 0 and m != None and int(m.group(1)) == 0
            )
        except subprocess.TimeoutExpired:
            return TestResult(False)
