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
    def get_exact_match_sample(cls):
        bug = TestEvaluatePatches.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestEvaluatePatches.PROMPT_STRATEGY,
            model_name=TestEvaluatePatches.MODEL_NAME,
        )
        sample["generation"] = [sample["fixed_code"] + "\n// comment"]
        return bug, sample

    @classmethod
    def get_ast_match_sample(cls):
        bug = TestEvaluatePatches.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestEvaluatePatches.PROMPT_STRATEGY,
            model_name=TestEvaluatePatches.MODEL_NAME,
        )
        sample["generation"] = [
            """    public LegendItemCollection getLegendItems() {
        LegendItemCollection result = new LegendItemCollection();
        if (this.plot == null) {
            return result;
        }
        int index = this.plot.getIndexOf(this);
        CategoryDataset dataset = this.plot.getDataset(index);
        if (dataset == null)
        {
            return result;
        }
        int seriesCount = dataset.getRowCount();
        if (plot.getRowRenderingOrder().equals(SortOrder.ASCENDING)) {
            for (int i = 0; i < seriesCount; i++) {
                if (isSeriesVisibleInLegend(i)) {
                    LegendItem item = getLegendItem(index, i);
                    if (item != null) {
                        result.add(item);
                    }
                }
            }
        }
        else {
            for (int i = seriesCount - 1; i >= 0; i--) {
                if (isSeriesVisibleInLegend(i)) {
                    LegendItem item = getLegendItem(index, i);
                    if (item != null) {
                        result.add(item);
                    }
                }
            }
        }
        return result;
    }
"""
        ]
        return bug, sample

    @classmethod
    def get_incorrect_sample(cls):
        bug = TestEvaluatePatches.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestEvaluatePatches.PROMPT_STRATEGY,
            model_name=TestEvaluatePatches.MODEL_NAME,
        )
        sample["generation"] = [sample["buggy_code"]]
        return bug, sample

    def test_exact_match_patch(self):
        bug, sample = TestEvaluatePatches.get_exact_match_sample()

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
        assert sample["evaluation"][0]["ast_match"] == True

    def test_ast_match_patch(self):
        bug, sample = TestEvaluatePatches.get_ast_match_sample()

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
        assert sample["evaluation"][0]["exact_match"] == False

    def test_incorrect_patch(self):
        bug, sample = TestEvaluatePatches.get_incorrect_sample()

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
        assert sample["evaluation"][0]["ast_match"] == False
