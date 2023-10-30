from evaluate_patches import evaluate_candidate
from generate_samples import generate_sample
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.benchmarks.benchmark import Benchmark


class TestEvaluatePatches:
    DEFECTS4J: Benchmark
    PROMPT_STRATEGY: str = "zero-shot-cloze"
    MODEL_NAME: str = "incoder"
    EVALUATE_STRATEGY: str = "replace"

    @classmethod
    def setup_class(cls):
        TestEvaluatePatches.DEFECTS4J = get_benchmark("defects4j")
        assert TestEvaluatePatches.DEFECTS4J is not None
        TestEvaluatePatches.DEFECTS4J.initialize()

    @classmethod
    def get_correct_sample(cls):
        bug = TestEvaluatePatches.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestEvaluatePatches.PROMPT_STRATEGY,
            model_name=TestEvaluatePatches.MODEL_NAME,
        )
        sample["generation"] = [sample["fixed_code"]]
        return bug, sample

    @classmethod
    def get_buggy_sample(cls):
        bug = TestEvaluatePatches.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestEvaluatePatches.PROMPT_STRATEGY,
            model_name=TestEvaluatePatches.MODEL_NAME,
        )
        sample["generation"] = [sample["buggy_code"]]
        return bug, sample

    def test_correct_patch(self):
        bug, sample = TestEvaluatePatches.get_correct_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            strategy=TestEvaluatePatches.EVALUATE_STRATEGY,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == True
        assert sample["evaluation"][0]["exact_match"] == True

    def test_buggy_patch(self):
        bug, sample = TestEvaluatePatches.get_buggy_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            strategy=TestEvaluatePatches.EVALUATE_STRATEGY,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == False
        assert sample["evaluation"][0]["exact_match"] == False
