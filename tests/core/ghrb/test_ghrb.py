from elleelleaime.core.utils.benchmarks import get_benchmark


class TestGHRB:
    def test_get_benchmark(self):
        ghrb = get_benchmark("ghrb")
        assert ghrb is not None
        ghrb.initialize()

        bugs = ghrb.get_bugs()

        assert bugs is not None
        assert len(bugs) > 0

    def test_checkout(self):
        pass

    def test_run_buggy(self):
        pass

    def test_run_fixed(self):
        pass
