from elleelleaime.core.utils.benchmarks import get_benchmark

from pathlib import Path
import uuid


class TestGHRB:
    def test_get_benchmark(self):
        ghrb = get_benchmark("ghrb")
        assert ghrb is not None
        ghrb.initialize()

        bugs = ghrb.get_bugs()

        assert bugs is not None
        assert len(bugs) == 76
        assert len(set([bug.pid for bug in bugs])) == 16

    def test_checkout(self):
        ghrb = get_benchmark("ghrb")
        assert ghrb is not None
        ghrb.initialize()

        # Sample a bug
        bug = ghrb.get_bugs().pop()

        buggy_path = f"/tmp/elleelleaime/{bug.get_identifier()}-buggy-{uuid.uuid4()}"
        fixed_path = f"/tmp/elleelleaime/{bug.get_identifier()}-fixed-{uuid.uuid4()}"
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
        bug = ghrb.get_bug("assertj-3")
        assert bug is not None

        buggy_path = f"/tmp/elleelleaime/{bug.get_identifier()}-buggy-{uuid.uuid4()}"
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
        bug = ghrb.get_bug("assertj-3")
        assert bug is not None

        fixed_path = f"/tmp/elleelleaime/{bug.get_identifier()}-fixed-{uuid.uuid4()}"
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

    def test_run_all_bugs(self):
        ghrb = get_benchmark("ghrb")
        assert ghrb is not None
        ghrb.initialize()

        # Sample a bug
        for bug in ghrb.get_bugs():
            print(bug.get_identifier())

            fixed_path = (
                f"/tmp/elleelleaime/{bug.get_identifier()}-fixed-{uuid.uuid4()}"
            )
            try:
                # Checkout fixed version
                bug.checkout(fixed_path, fixed=True)

                # Compile fixed version
                compile_result = bug.compile(fixed_path)
                if not compile_result.is_passing():
                    print(f"Bug {bug.get_identifier()} (fixed) failed to compile")

                # Test fixed version
                test_result = bug.test(fixed_path)
                if not test_result.is_passing():
                    print(f"Bug {bug.get_identifier()} (fixed) failed to test")
            finally:
                bug.cleanup(fixed_path)

            buggy_path = (
                f"/tmp/elleelleaime/{bug.get_identifier()}-buggy-{uuid.uuid4()}"
            )
            try:
                # Checkout buggy version
                bug.checkout(buggy_path, fixed=True)

                # Compile buggy version
                compile_result = bug.compile(buggy_path)
                if not compile_result.is_passing():
                    print(f"Bug {bug.get_identifier()} (buggy) failed to compile")

                # Test buggy version
                test_result = bug.test(buggy_path)
                if test_result.is_passing():
                    print(f"Bug {bug.get_identifier()} (buggy) passed tests")
            finally:
                bug.cleanup(buggy_path)
