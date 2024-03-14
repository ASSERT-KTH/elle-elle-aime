from generate_samples import generate_sample
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.benchmarks.benchmark import Benchmark


class TestFillInTheMiddleSamplesSantaCoder:
    DEFECTS4J: Benchmark
    PROMPT_STRATEGY: str = "fill-in-the-middle"
    MODEL_NAME: str = "santacoder"

    @classmethod
    def setup_class(cls):
        TestFillInTheMiddleSamplesSantaCoder.DEFECTS4J = get_benchmark("defects4j")
        assert TestFillInTheMiddleSamplesSantaCoder.DEFECTS4J is not None
        TestFillInTheMiddleSamplesSantaCoder.DEFECTS4J.initialize()

    def test_closure_46(self):
        bug = TestFillInTheMiddleSamplesSantaCoder.DEFECTS4J.get_bug("Closure-46")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestFillInTheMiddleSamplesSantaCoder.PROMPT_STRATEGY,
            model_name=TestFillInTheMiddleSamplesSantaCoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Closure-46"
        assert sample["prompt_strategy"] == "fill-in-the-middle"

        # Not supported since it changes the annotation too (outside the method declaration)
        assert sample["prompt"] is None

    def test_closure_115(self):
        bug = TestFillInTheMiddleSamplesSantaCoder.DEFECTS4J.get_bug("Closure-115")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestFillInTheMiddleSamplesSantaCoder.PROMPT_STRATEGY,
            model_name=TestFillInTheMiddleSamplesSantaCoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Closure-115"
        assert sample["prompt_strategy"] == "fill-in-the-middle"

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
                "<fim-prefix>  private CanInlineResult canInlineReferenceDirectly("
            )
        )
        assert sample["prompt"].endswith("<fim-middle>")
        assert sample["prompt"].count("<fim-prefix>") == 1
        assert sample["prompt"].count("<fim-middle>") == 1
        assert sample["prompt"].count("<fim-suffix>") == 1
