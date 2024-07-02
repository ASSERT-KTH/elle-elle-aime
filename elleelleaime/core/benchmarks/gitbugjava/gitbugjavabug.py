import subprocess
import backoff
import shutil
import re
import sys
import os
from elleelleaime.core.benchmarks.benchmark import Benchmark

from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.benchmarks.test_result import TestResult
from elleelleaime.core.benchmarks.compile_result import CompileResult


class GitBugJavaBug(Bug):
    """
    The class for representing GitBugJava bugs
    """

    def __init__(self, benchmark: Benchmark, bid: str, ground_truth: str) -> None:
        self.bid = bid
        super().__init__(benchmark, bid, ground_truth)

    @backoff.on_exception(
        backoff.constant, subprocess.CalledProcessError, interval=1, max_tries=3
    )
    def checkout(self, path: str, fixed: bool = False) -> bool:
        # Remove the directory if it exists
        # shutil.rmtree(path, ignore_errors=True)

        # Checkout the bug
        args = [sys.executable, self.benchmark.get_bin(), "checkout", self.bid, path]
        if fixed:
            args.append(" --fixed")
        checkout_run = subprocess.run(
            args,
            capture_output=True,
            check=True,
        )
        return checkout_run.returncode == 0

        # TODO: Not sure if this is required...
        # Convert line endings to unix
        # command = f"find {path} -type f -print0 | xargs -0 -n 1 -P 4 dos2unix"
        # dos2unix_run = subprocess.run(
        #     command, shell=True, capture_output=True, check=True
        # )
        # return checkout_run.returncode == 0 and dos2unix_run.returncode == 0

    def compile(self, path: str) -> CompileResult:
        # TODO: WTF do i do here?
        return CompileResult(True)

    def test(self, path: str) -> TestResult:
        # First run only relevant tests
        env = os.environ.copy()  # act binary used by gitbug-java should be in PATH
        args = [sys.executable, self.benchmark.get_bin(), "run", path]
        test_run = subprocess.run(
            args,
            capture_output=True,
            timeout=60*3,
            env=env,
        )
        return TestResult(test_run.returncode == 0)
