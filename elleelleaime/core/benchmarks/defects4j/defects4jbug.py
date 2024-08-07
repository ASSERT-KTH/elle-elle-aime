import subprocess
import shutil
import re
import os

from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.bug import RichBug
from elleelleaime.core.benchmarks.test_result import TestResult
from elleelleaime.core.benchmarks.compile_result import CompileResult


class Defects4JBug(RichBug):
    """
    The class for representing Defects4J bugs
    """

    def __init__(
        self,
        benchmark: Benchmark,
        pid: str,
        bid: str,
        ground_truth: str,
        failing_tests: dict[str, str],
    ) -> None:
        self.pid = pid
        self.bid = bid
        super().__init__(
            benchmark,
            f"{pid}-{bid}",
            ground_truth,
            failing_tests,
            ground_truth_inverted=True,
        )

    def __run_defects4j_with_path(
        self, command: str, path: str, check: bool = True
    ) -> subprocess.CompletedProcess[bytes]:
        options = f"--volume '{path}:{path}' --workdir '{path}'"
        chown = f"chown -R {os.getuid()}:{os.getgid()} {path} && chown -R {os.getuid()}:{os.getgid()} /defects4j"
        gosu = f"gosu {os.getuid()}:{os.getgid()}"

        subp_command = f"{self.benchmark.get_bin(options)} /bin/bash -c '{chown} && {gosu} {command}'"

        return subprocess.run(
            subp_command,
            shell=True,
            capture_output=True,
            check=check,
        )

    def checkout(self, path: str, fixed: bool = False) -> bool:
        # Remove the directory if it exists
        shutil.rmtree(path, ignore_errors=True)

        # Checkout the bug
        checkout_run = self.__run_defects4j_with_path(
            f"defects4j checkout -p {self.pid} -v {self.bid}{'f' if fixed else 'b'} -w {path}",
            path,
        )

        # Convert line endings to unix
        dos2unix_run = subprocess.run(
            f"find {path} -type f -print0 | xargs -0 -n 1 -P 4 dos2unix",
            shell=True,
            capture_output=True,
            check=True,
        )

        return checkout_run.returncode == 0 and dos2unix_run.returncode == 0

    def compile(self, path: str) -> CompileResult:
        run = self.__run_defects4j_with_path(
            f"timeout {5*60} defects4j compile",
            path=path,
            check=False,
        )
        return CompileResult(run.returncode == 0)

    def test(self, path: str) -> TestResult:
        # First run only relevant tests
        run = self.__run_defects4j_with_path(
            f"timeout {30*60} defects4j test -r",
            path=path,
            check=False,
        )

        m = re.search(r"Failing tests: ([0-9]+)", run.stdout.decode("utf-8"))
        if not (run.returncode == 0 and m != None and int(m.group(1)) == 0):
            return TestResult(False)

        # Only run the whole test suite if the relevant tests pass
        run = self.__run_defects4j_with_path(
            f"timeout {30*60} defects4j test",
            path=path,
            check=False,
        )
        m = re.search(r"Failing tests: ([0-9]+)", run.stdout.decode("utf-8"))
        return TestResult(run.returncode == 0 and m != None and int(m.group(1)) == 0)

    def get_src_test_dir(self, path: str) -> str:
        run = self.__run_defects4j_with_path(
            "defects4j export -p dir.src.tests",
            path=path,
        )

        return run.stdout.decode("utf-8").strip()
