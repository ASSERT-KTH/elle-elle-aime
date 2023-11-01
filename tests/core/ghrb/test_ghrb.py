from elleelleaime.core.utils.benchmarks import get_benchmark

from pathlib import Path


class TestGHRB:
    def test_get_benchmark(self):
        ghrb = get_benchmark("ghrb")
        assert ghrb is not None
        ghrb.initialize()

        bugs = ghrb.get_bugs()

        assert bugs is not None
        assert len(bugs) > 0

    def test_checkout(self):
        ghrb = get_benchmark("ghrb")
        assert ghrb is not None
        ghrb.initialize()

        # Sample a bug
        bug = ghrb.get_bugs().pop()

        buggy_path = f"/tmp/elleelleaime/ghrb/{bug.get_identifier()}-buggy"
        fixed_path = f"/tmp/elleelleaime/ghrb/{bug.get_identifier()}-fixed"
        try:
            # Checkout buggy version
            bug.checkout(buggy_path, fixed=False)
            # Checkout fixed version
            bug.checkout(fixed_path, fixed=True)

            # Assert that there are files in the directories
            assert len(list(Path(buggy_path).glob("**/*"))) > 0
            assert len(list(Path(fixed_path).glob("**/*"))) > 0
        finally:
            bug.cleanup(buggy_path)
            bug.cleanup(fixed_path)

    def test_run_buggy(self):
        ghrb = get_benchmark("ghrb")
        assert ghrb is not None
        ghrb.initialize()

        # Sample a bug
        bug = ghrb.get_bugs().pop()

        buggy_path = f"/tmp/elleelleaime/ghrb/{bug.get_identifier()}-buggy"
        try:
            # Checkout buggy version
            bug.checkout(buggy_path, fixed=False)

            # Compile buggy version
            compile_result = bug.compile(buggy_path)
            assert compile_result.is_passing()

            # Test buggy version
            test_result = bug.test(buggy_path)
            assert not test_result.is_passing()
        finally:
            bug.cleanup(buggy_path)

    def test_run_fixed(self):
        ghrb = get_benchmark("ghrb")
        assert ghrb is not None
        ghrb.initialize()

        # Sample a bug
        bug = ghrb.get_bugs().pop()

        fixed_path = f"/tmp/elleelleaime/ghrb/{bug.get_identifier()}-fixed"
        try:
            # Checkout fixed version
            bug.checkout(fixed_path, fixed=True)

            # Compile fixed version
            compile_result = bug.compile(fixed_path)
            assert compile_result.is_passing()

            # Test fixed version
            test_result = bug.test(fixed_path)
            assert test_result.is_passing()
        finally:
            bug.cleanup(fixed_path)
