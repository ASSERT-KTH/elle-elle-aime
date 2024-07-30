from generate_samples import generate_sample
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.benchmarks.benchmark import Benchmark


class TestInstructPrompting:
    DEFECTS4J: Benchmark
    PROMPT_STRATEGY: str = "instruct"

    @classmethod
    def setup_class(cls):
        TestInstructPrompting.DEFECTS4J = get_benchmark("defects4j")
        assert TestInstructPrompting.DEFECTS4J is not None
        TestInstructPrompting.DEFECTS4J.initialize()

    def test_closure_115(self):
        bug = TestInstructPrompting.DEFECTS4J.get_bug("Closure-115")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestInstructPrompting.PROMPT_STRATEGY,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Closure-115"
        assert sample["prompt_strategy"] == "instruct"

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
            "/**\n   * Determines whether a function can be inlined at a particular call site."
            in sample["prompt"]
        )

    def test_closure_4(self):
        bug = TestInstructPrompting.DEFECTS4J.get_bug("Closure-4")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestInstructPrompting.PROMPT_STRATEGY,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Closure-4"
        assert sample["prompt_strategy"] == "instruct"

        # Assert that the buggy code and fixed code are properly separated
        assert "if (detectImplicitPrototypeCycle()) {" in sample["buggy_code"]
        assert "if (detectImplicitPrototypeCycle()) {" not in sample["fixed_code"]
        assert "if (detectInheritanceCycle()) {" not in sample["buggy_code"]
        assert "if (detectInheritanceCycle()) {" in sample["fixed_code"]

        # Assert that the prompt is properly constructed
        assert (
            "/**\n   * Resolve the referenced type within the enclosing scope.\n   */"
            in sample["prompt"]
        )
