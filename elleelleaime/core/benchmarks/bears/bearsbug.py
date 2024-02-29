import subprocess
import tempfile
import backoff
import shutil
import re
import os

from pathlib import Path
from uuid import uuid4

from elleelleaime.core.benchmarks.benchmark import Benchmark
from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.benchmarks.test_result import TestResult
from elleelleaime.core.benchmarks.compile_result import CompileResult


class BearsBug(Bug):
    """
    The class for representing Bears bugs
    """

    @backoff.on_exception(
        backoff.constant, subprocess.CalledProcessError, interval=1, max_tries=3
    )
    def checkout(self, path: str, fixed: bool = False) -> bool:
        try:
            # Remove the directory if it exists
            shutil.rmtree(path, ignore_errors=True)

            # Create the directory
            Path(path).mkdir(parents=True, exist_ok=True)

            # Copy the benchmark elsewhere to avoid conflicts
            temp_benchmark_path = Path(
                tempfile.gettempdir(), "elleelleaime", str(uuid4())
            )
            shutil.copytree(
                self.benchmark.get_path(), temp_benchmark_path, dirs_exist_ok=True
            )
            # We must copy also the .git directory
            os.remove(Path(temp_benchmark_path, ".git/"))
            shutil.copytree(
                Path(self.benchmark.get_path(), "../../.git/modules/benchmarks/bears"),
                Path(temp_benchmark_path, ".git/"),
                dirs_exist_ok=True,
            )
            # And remove the worktree from the config file
            # Remove "	worktree = ../../../../benchmarks/bears" from the config file using sed
            config_path = Path(temp_benchmark_path, ".git", "config")
            sed_run = subprocess.run(
                f"sed -i '/worktree = \.\.\/\.\.\/\.\.\/\.\.\/benchmarks\/bears/d' {config_path}",
                shell=True,
                capture_output=True,
                check=True,
            )

            # Run checkout script
            checkout_run = subprocess.run(
                f"cd {temp_benchmark_path} && python scripts/checkout_bug.py --bugId {self.identifier} --workspace {path}",
                shell=True,
                capture_output=True,
                check=True,
            )

            # Checkout the fixed version if needed
            if fixed:
                subprocess.run(
                    f"cd {path} && git checkout -",
                    shell=True,
                    capture_output=True,
                    check=True,
                )

            return sed_run.returncode == 0 and checkout_run.returncode == 0
        finally:
            # Remove the temporary directory
            shutil.rmtree(temp_benchmark_path, ignore_errors=True)

    def compile(self, path: str) -> CompileResult:
        run = subprocess.run(
            f"cd {self.benchmark.get_path()} && python scripts/compile_bug.py --bugId {self.identifier} --workspace {path}",
            shell=True,
            capture_output=True,
        )
        return CompileResult(run.returncode == 0)

    def test(self, path: str) -> TestResult:
        run = subprocess.run(
            f"cd {self.benchmark.get_path()} && python scripts/run_tests_bug.py --bugId {self.identifier} --workspace {path}",
            shell=True,
            capture_output=True,
        )
        return TestResult(run.returncode == 0)
