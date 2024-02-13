from generate_breaker_samples import generate_breaker_samples
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.benchmarks.benchmark import Benchmark


class TestGenerateBreakerSamples:
    QUIXBUGS: Benchmark
    SAMPLE_STRATEGY: str = "mufin-breaker"
    MODEL_NAME: str = "starcoder"

    @classmethod
    def setup_class(cls):
        TestGenerateBreakerSamples.QUIXBUGS = get_benchmark("quixbugs")
        assert TestGenerateBreakerSamples.QUIXBUGS is not None
        TestGenerateBreakerSamples.QUIXBUGS.initialize()

    def test_BITCOUNT(self):
        bug = TestGenerateBreakerSamples.QUIXBUGS.get_bug("BITCOUNT")
        assert bug is not None

        samples = generate_breaker_samples(
            bug=bug,
            sample_strategy=TestGenerateBreakerSamples.SAMPLE_STRATEGY,
            model_name=TestGenerateBreakerSamples.MODEL_NAME,
        )

        assert len(samples) == 21

    def test_SHORTEST_PATHS(self):
        bug = TestGenerateBreakerSamples.QUIXBUGS.get_bug("SHORTEST_PATHS")
        assert bug is not None

        samples = generate_breaker_samples(
            bug=bug,
            sample_strategy=TestGenerateBreakerSamples.SAMPLE_STRATEGY,
            model_name=TestGenerateBreakerSamples.MODEL_NAME,
        )

        assert len(samples) == 190
