import subprocess
import re
from elleelleaime.core.benchmarks.benchmark import Benchmark

from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.benchmarks.test_result import TestResult
from elleelleaime.core.benchmarks.compile_result import CompileResult

class Defects4JBug(Bug):
    """
    The class for representing Defects4J bugs
    """

    def __init__(self, benchmark: Benchmark, pid: str, bid: str) -> None:
        self.pid = pid
        self.bid = bid
        super().__init__(benchmark, f"{pid}-{bid}")

    def checkout(self, path: str, fixed: bool = False) -> bool:
        run = subprocess.run(f"{self.benchmark.get_bin()} checkout -p {self.pid} -v {self.bid}{'f' if fixed else 'b'} -w {path}", 
                             shell=True, capture_output=True, check=True)
        run = subprocess.run(f"find {path} -type f -print0 | xargs -0 -n 1 -P 4 dos2unix", 
                             shell=True, capture_output=True, check=True)
        return run.returncode == 0


    def apply_diff(self, path: str) -> bool:
        return super().apply_diff(path)


    def compile(self, path: str) -> CompileResult:
        run = subprocess.run("cd %s; timeout 60 defects4j compile" % path, shell=True, capture_output=True)
        return CompileResult(True, run.returncode == 0)


    def test(self, path: str) -> TestResult:
        run = subprocess.run("cd %s; timeout 600 defects4j test" % path, shell=True, capture_output=True)
        m = re.search(r"Failing tests: ([0-9]+)", run.stdout.decode("utf-8"))
        return TestResult(m != None, run.returncode == 0 and m != None and int(m.group(1)) == 0)