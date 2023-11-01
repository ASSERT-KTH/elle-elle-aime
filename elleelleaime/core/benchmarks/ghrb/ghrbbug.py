import subprocess
import backoff
import shutil
import re
from elleelleaime.core.benchmarks.benchmark import Benchmark

from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.benchmarks.test_result import TestResult
from elleelleaime.core.benchmarks.compile_result import CompileResult


class GHRBBug(Bug):
    """
    The class for representing GHRB bugs
    """

    def __init__(
        self, benchmark: Benchmark, pid: str, bid: str, ground_truth: str
    ) -> None:
        self.pid = pid
        self.bid = bid
        super().__init__(benchmark, f"{pid}-{bid}", ground_truth)

    @backoff.on_exception(
        backoff.constant, subprocess.CalledProcessError, interval=1, max_tries=3
    )
    def checkout(self, path: str, fixed: bool = False) -> bool:
        # Remove the directory if it exists
        self.cleanup(path)

        # Checkout the bug
        # Note: we have to cd into the benchmark directory because of hardcoded paths in the GHRB CLI
        checkout_run = subprocess.run(
            f"cd {self.benchmark.get_path()} && {self.benchmark.get_bin()} \"./cli.py checkout -p {self.pid} -v {self.bid}{'f' if fixed else 'b'} -w {path}\"",
            shell=True,
            capture_output=True,
            check=True,
        )

        return checkout_run.returncode == 0

    def cleanup(self, path: str) -> bool:
        try:
            # Note: we have to cd into the benchmark directory because of hardcoded paths in the GHRB CLI
            # We must remove with the docker command due to permission issues
            rm_run = subprocess.run(
                f'cd {self.benchmark.get_path()} && {self.benchmark.get_bin()} "rm -rf {path}"',
                shell=True,
                capture_output=True,
                check=True,
            )
            return rm_run.returncode == 0
        finally:
            shutil.rmtree(path, ignore_errors=True)

    def apply_diff(self, path: str) -> bool:
        return super().apply_diff(path)

    def compile(self, path: str) -> CompileResult:
        # Note: we have to cd into the benchmark directory because of hardcoded paths in the GHRB CLI
        run = subprocess.run(
            f'cd {self.benchmark.get_path()} && timeout {5*60} {self.benchmark.get_bin()} "./cli.py compile -w {path}"',
            shell=True,
            capture_output=True,
        )
        return CompileResult(run.returncode == 0)

    def test(self, path: str) -> TestResult:
        # Note: we have to cd into the benchmark directory because of hardcoded paths in the GHRB CLI
        run = subprocess.run(
            f'cd {self.benchmark.get_path()} && timeout {30*60} {self.benchmark.get_bin()} "./cli.py test -w {path}"',
            shell=True,
            capture_output=True,
        )
        m_stdout = re.search(r"Failure\/Error info", run.stdout.decode("utf-8"))
        m_stderr = re.search(r"Failure\/Error info", run.stderr.decode("utf-8"))
        return TestResult(run.returncode == 0 and m_stdout is None and m_stderr is None)
