from generate_mufin_samples import generate_mufin_samples
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

        samples = generate_mufin_samples(
            bug=bug,
            sample_strategy=TestGenerateBreakerSamples.SAMPLE_STRATEGY,
            model_name=TestGenerateBreakerSamples.MODEL_NAME,
        )

        assert len(samples) == 21

    def test_SHORTEST_PATHS(self):
        bug = TestGenerateBreakerSamples.QUIXBUGS.get_bug("SHORTEST_PATHS")
        assert bug is not None

        samples = generate_mufin_samples(
            bug=bug,
            sample_strategy=TestGenerateBreakerSamples.SAMPLE_STRATEGY,
            model_name=TestGenerateBreakerSamples.MODEL_NAME,
        )

        assert len(samples) == 190


class TestGenerateEvalSamples:
    DEFECTS4J: Benchmark
    SAMPLE_STRATEGY: str = "mufin-eval"
    MODEL_NAME: str = "starcoder"

    @classmethod
    def setup_class(cls):
        TestGenerateEvalSamples.DEFECTS4J = get_benchmark("defects4j")
        assert TestGenerateEvalSamples.DEFECTS4J is not None
        TestGenerateEvalSamples.DEFECTS4J.initialize()

    def test_closure_115(self):
        bug = TestGenerateEvalSamples.DEFECTS4J.get_bug("Closure-115")
        assert bug is not None

        sample = generate_mufin_samples(
            bug=bug,
            sample_strategy=TestGenerateEvalSamples.SAMPLE_STRATEGY,
            model_name=TestGenerateEvalSamples.MODEL_NAME,
        )[0]

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Closure-115"
        assert sample["prompt_strategy"] == "mufin-eval"

        # Assert that the buggy code and fixed code are properly separated
        assert "boolean hasSideEffects = false;" in sample["buggy_code"]
        assert "boolean hasSideEffects = false;" not in sample["fixed_code"]
        assert (
            "if (hasSideEffects && NodeUtil.canBeSideEffected(cArg)) {"
            in sample["buggy_code"]
        )
        assert (
            "if (hasSideEffects && NodeUtil.canBeSideEffected(cArg)) {"
            not in sample["fixed_code"]
        )

        # Assert that the prompt is properly constructed
        assert (
            sample["prompt"]
            .strip()
            .startswith(
                "<FIXER><fim_prefix>  private CanInlineResult canInlineReferenceDirectly("
            )
        )
        assert sample["prompt"].endswith("<fim_middle>")
        assert sample["prompt"].count("<fim_prefix>") == 1
        assert sample["prompt"].count("<fim_middle>") == 1
        assert sample["prompt"].count("<fim_suffix>") == 1
