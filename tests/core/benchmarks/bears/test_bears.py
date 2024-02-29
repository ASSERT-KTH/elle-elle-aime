from elleelleaime.core.utils.benchmarks import get_benchmark

from pathlib import Path
import uuid
import shutil
import tqdm
import concurrent.futures


class TestBears:
    def test_get_benchmark(self):
        bears = get_benchmark("bears")
        assert bears is not None
        bears.initialize()

        bugs = bears.get_bugs()

        assert bugs is not None
        assert len(bugs) == 118
        assert len(set([bug.get_identifier() for bug in bugs])) == 118

    def test_checkout(self):
        bears = get_benchmark("bears")
        assert bears is not None
        bears.initialize()

        bugs = list(bears.get_bugs())[:10]
        assert bugs is not None

        for bug in bugs:
            buggy_path = (
                f"/tmp/elleelleaime/{bug.get_identifier()}-buggy-{uuid.uuid4()}"
            )
            fixed_path = (
                f"/tmp/elleelleaime/{bug.get_identifier()}-fixed-{uuid.uuid4()}"
            )
            try:
                # Checkout buggy version
                ret = bug.checkout(buggy_path, fixed=False)
                assert ret
                # Checkout fixed version
                ret = bug.checkout(fixed_path, fixed=True)
                assert ret

                # Assert that there are files in the directories
                assert len(list(Path(buggy_path).glob("**/*"))) > 0
                assert len(list(Path(fixed_path).glob("**/*"))) > 0

                # Assert that we can reach the java file
                assert Path(buggy_path, "pom.xml").exists()
                assert Path(fixed_path, "pom.xml").exists()
            finally:
                shutil.rmtree(buggy_path, ignore_errors=True)
                shutil.rmtree(fixed_path, ignore_errors=True)

    def test_run_all_bugs(self):
        bears = get_benchmark("bears")
        assert bears is not None
        bears.initialize()

        # This test takes a while, so we limit to 10 bugs.
        # Remove the slice to run all bugs.
        bugs = list(bears.get_bugs())[:10]
        assert bugs is not None

        def run_bug(bug):
            buggy_path = (
                f"/tmp/elleelleaime/{bug.get_identifier()}-buggy-{uuid.uuid4()}"
            )
            fixed_path = (
                f"/tmp/elleelleaime/{bug.get_identifier()}-fixed-{uuid.uuid4()}"
            )

            try:
                # Checkout buggy version
                ret = bug.checkout(buggy_path, fixed=False)
                assert ret, "Failed checkout for {bug.get_identifier()}-buggy"
                # Checkout fixed version
                ret = bug.checkout(fixed_path, fixed=True)
                assert ret, f"Failed checkout for {bug.get_identifier()}-fixed"

                # Compile buggy version
                compile_result = bug.compile(buggy_path)
                if not compile_result.is_passing():
                    return False

                # Test buggy version
                test_result = bug.test(buggy_path)
                if test_result.is_passing():
                    return False

                # Compile fixed version
                compile_result = bug.compile(fixed_path)
                if not compile_result.is_passing():
                    return False

                # Test fixed version
                test_result = bug.test(fixed_path)
                if not test_result.is_passing():
                    return False

                return True
            finally:
                shutil.rmtree(buggy_path, ignore_errors=True)
                shutil.rmtree(fixed_path, ignore_errors=True)

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            futures_to_bugs = {}
            for bug in bugs:
                # Submit the bug to be tested as a separate task
                futures.append(executor.submit(run_bug, bug))
                futures_to_bugs[futures[-1]] = bug
            # Wait for all tasks to complete
            for future in tqdm.tqdm(concurrent.futures.as_completed(futures)):
                result = future.result()
                if not result:
                    assert (
                        result
                    ), f"Failed for {futures_to_bugs[future].get_identifier()}"
