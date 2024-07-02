from typing import Generator
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.benchmarks.bug import Bug

from pathlib import Path
import shutil
import pytest
import uuid
import tqdm
import concurrent.futures


class TestGitBugJava:

    @pytest.fixture(autouse=True, scope="class")
    def tmp_root(self) -> Generator[Path, None, None]:
        # Create a temporary directory for the tests with a random identifier
        tmp_root_path = Path("/tmp").joinpath(
            f"test-elleelleamie-gitbugjava-{uuid.uuid4()}"
        )
        tmp_root_path.mkdir(parents=True, exist_ok=True)
        print(f"Created temporary directory: {tmp_root_path}")
        yield tmp_root_path
        print(f"Removing temporary directory: {tmp_root_path}")
        shutil.rmtree(tmp_root_path, ignore_errors=True)

    def checkout_bug(self, bug: Bug, tmp_root: Path) -> bool:
        buggy_path = tmp_root.joinpath(f"{bug.get_identifier()}-buggy-{uuid.uuid4()}")
        fixed_path = tmp_root.joinpath(f"{bug.get_identifier()}-fixed-{uuid.uuid4()}")

        try:
            # Checkout buggy version
            assert bug.checkout(
                buggy_path, fixed=False
            ), f"Failed to checkout buggy {bug.get_identifier()}"
            # Checkout fixed version
            assert bug.checkout(
                fixed_path, fixed=True
            ), f"Failed to checkout fixed {bug.get_identifier()}"
            # Assert that there are files in the directories
            if list(buggy_path.glob("**/*")) == 0:
                return False
            if list(fixed_path.glob("**/*")) == 0:
                return False

            return True
        finally:
            shutil.rmtree(buggy_path, ignore_errors=True)
            shutil.rmtree(fixed_path, ignore_errors=True)

    def run_bug(self, bug: Bug, tmp_root: Path) -> bool:
        buggy_path = tmp_root.joinpath(f"{bug.get_identifier()}-buggy-{uuid.uuid4()}")
        fixed_path = tmp_root.joinpath(f"{bug.get_identifier()}-fixed-{uuid.uuid4()}")

        try:
            # Checkout buggy version
            # assert bug.checkout(
            #     buggy_path, fixed=False
            # ), f"Failed to checkout buggy {bug.get_identifier()}"
            # TODO: gitbug-java does not have a test command
            # Compile buggy version
            # compile_result = bug.compile(buggy_path)
            # if not compile_result.is_passing():
            #     return False
            # Test buggy version
            # test_result = bug.test(buggy_path)
            # if test_result.is_passing():
            #     return False

            # Checkout fixed version
            assert bug.checkout(
                fixed_path, fixed=True
            ), f"Failed to checkout fixed {bug.get_identifier()}"
            # Compile fixed version
            # TODO: WTF do i do here? (same in the bug class)
            # compile_result = bug.compile(fixed_path)
            # if not compile_result.is_passing():
            #     return False
            # Test fixed version
            test_result = bug.test(fixed_path)
            if not test_result.is_passing():
                return False

            return True
        finally:
            shutil.rmtree(buggy_path, ignore_errors=True)
            shutil.rmtree(fixed_path, ignore_errors=True)

    def test_get_benchmark(self):
        benchmark = get_benchmark("GitBugJava")
        assert benchmark is not None
        benchmark.initialize()

        bugs = benchmark.get_bugs()
        assert bugs is not None

    def test_checkout_bugs(self, tmp_root: Path):
        benchmark = get_benchmark("GitBugJava")
        assert benchmark is not None
        benchmark.initialize()

        # Run only the first 3 bugs to not take too long
        bugs = list(benchmark.get_bugs())[:3]
        assert bugs is not None

        for bug in bugs:
            assert self.checkout_bug(
                bug, tmp_root
            ), f"Failed checkout for {bug.get_identifier()}"

    def test_run_bugs(self, tmp_root: Path):
        benchmark = get_benchmark("GitBugJava")
        assert benchmark is not None
        benchmark.initialize()

        # Run only the first 3 bugs to not take too long
        bugs = list(benchmark.get_bugs())[:1]
        assert bugs is not None

        # Checkout and test bugs
        for bug in bugs:
            assert self.run_bug(bug, tmp_root), f"Failed run for {bug.get_identifier()}"

    @pytest.mark.skip(reason="This test is too slow to run on CI.")
    def test_run_all_bugs(self, tmp_root: Path):
        benchmark = get_benchmark("GitBugJava")
        assert benchmark is not None
        benchmark.initialize()

        # Run only the first 3 bugs to not take too long
        bugs = list(benchmark.get_bugs())
        assert bugs is not None

        # Checkout and test bugs
        for bug in bugs:
            assert self.run_bug(bug, tmp_root), f"Failed run for {bug.get_identifier()}"
