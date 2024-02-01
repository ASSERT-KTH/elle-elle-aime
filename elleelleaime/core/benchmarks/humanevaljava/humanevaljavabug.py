import subprocess
import shutil

from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.benchmarks.test_result import TestResult
from elleelleaime.core.benchmarks.compile_result import CompileResult


class HumanEvalJavaBug(Bug):
    """
    The class for representing HumanEvalJava bugs
    """

    def checkout(self, path: str, fixed: bool = False) -> bool:
        # Remove the directory if it exists
        shutil.rmtree(path, ignore_errors=True)
        # Make the directory
        subprocess.run(
            f"mkdir -p {path}",
            shell=True,
            capture_output=True,
            check=True,
        )

        # Checkout the bug is the same as copying the entire benchmark
        checkout_run = subprocess.run(
            f"cp -r {self.benchmark.get_path()}/* {path}",
            shell=True,
            capture_output=True,
            check=True,
        )

        # If we want the fixed version, we replace the buggy program with the correct one
        # This way we can always use the same path and the same build script
        if fixed:
            shutil.copyfile(
                f"{path}/src/main/java/humaneval/correct/{self.get_identifier()}.java",
                f"{path}/src/main/java/humaneval/buggy/{self.get_identifier()}.java",
            )

            # We only needd to change the package name
            subprocess.run(
                f"sed -i 's/package humaneval\\.correct/package humaneval\\.buggy/g' {path}/src/main/java/humaneval/buggy/{self.get_identifier()}.java",
                shell=True,
                capture_output=True,
                check=True,
            )

        return checkout_run.returncode == 0

    def compile(self, path: str) -> CompileResult:
        run = subprocess.run(
            f"cd {path}; timeout {5*60} mvn compile",
            shell=True,
            capture_output=True,
        )
        return CompileResult(run.returncode == 0)

    def test(self, path: str) -> TestResult:
        run = subprocess.run(
            f"cd {path}; timeout {30*60} mvn test -Dtest=TEST_{self.get_identifier()}",
            shell=True,
            capture_output=True,
        )
        return TestResult(run.returncode == 0)
