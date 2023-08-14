from elleelleaime.generate_samples import generate_sample
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.benchmarks.benchmark import Benchmark


class TestClozeSamplesIncoder:
    """
    We test the generation of cloze prompts for several types of bug fixes.
    We only generate samples for bugs that are single-function and single-file.
    
    We test the following types of bug fixes:
        - Addition only
            - Single-Hunk
                - N continuous lines
                - N non-continous lines  (Lang-3)
                - Whole function (Chart-23)
            - Multi-Hunk 
                - N hunks of addition only
        
        - Removal only
            - Single-Hunk
                - N continuous lines
                - N non-continous lines
                - Whole function
            - Multi-Hunk
                - N hunks of removal only (Lang-10) (failing)
        
        - Addition and removal
            - Single-Hunk
                - N continuous lines (Chart-6)
                - N non-continuous lines (Closure-101)
            - Multi-Hunk
                - N hunks of addition and removal
    """
    DEFECTS4J: Benchmark
    PROMPT_STRATEGY: str = "zero-shot-cloze"
    MODEL_NAME: str = "incoder"

    @classmethod
    def setup_class(cls):
        TestClozeSamplesIncoder.DEFECTS4J = get_benchmark("defects4j")
        assert TestClozeSamplesIncoder.DEFECTS4J is not None
        TestClozeSamplesIncoder.DEFECTS4J.initialize()

    def test_chart_6(self):
        bug = TestClozeSamplesIncoder.DEFECTS4J.get_bug("Chart-6")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesIncoder.PROMPT_STRATEGY,
            model_name=TestClozeSamplesIncoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Chart-6"
        assert sample["prompt_strategy"] == "zero-shot-cloze"
        
        print(sample["buggy_code"])
        print(sample["fixed_code"])
        print(sample["prompt"])

        # Assert that the buggy code and fixed code are properly separated
        assert "return super.equals(obj);" in sample["buggy_code"]
        assert "return super.equals(obj);" not in sample["fixed_code"]
        assert not "ShapeList that = (ShapeList) obj;" in sample["buggy_code"]
        assert "ShapeList that = (ShapeList) obj;" in sample["fixed_code"]

        # Assert that the prompt is properly constructed
        assert (
            sample["prompt"]
            .strip()
            .startswith(
                "public boolean equals(Object obj) {"
            )
        )
        assert sample["prompt"].count("<|mask:") == 1
        assert sample["prompt"].count("<|mask:0|>") == 1

    def test_lang_3(self):
        bug = TestClozeSamplesIncoder.DEFECTS4J.get_bug("Lang-3")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesIncoder.PROMPT_STRATEGY,
            model_name=TestClozeSamplesIncoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Lang-3"
        assert sample["prompt_strategy"] == "zero-shot-cloze"

        # Assert that the buggy code and fixed code are properly separated
        assert not "if(numDecimals <= 7){" in sample["buggy_code"]
        assert "if(numDecimals <= 7){" in sample["fixed_code"]

        # Assert that the prompt is properly constructed
        assert (
            sample["prompt"]
            .strip()
            .startswith(
                "public static Number createNumber(final String str) throws NumberFormatException"
            )
        )
        assert sample["prompt"].count("<|mask:") == 4
        assert sample["prompt"].count("<|mask:0|>") == 1
        assert sample["prompt"].count("<|mask:1|>") == 1
        assert sample["prompt"].count("<|mask:2|>") == 1
        assert sample["prompt"].count("<|mask:3|>") == 1

    def test_closure_101(self):
        bug = TestClozeSamplesIncoder.DEFECTS4J.get_bug("Closure-101")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesIncoder.PROMPT_STRATEGY,
            model_name=TestClozeSamplesIncoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Closure-101"
        assert sample["prompt_strategy"] == "zero-shot-cloze"

        # Assert that the buggy code and fixed code are properly separated
        assert (
            not "options.closurePass = flags.process_closure_primitives;"
            in sample["buggy_code"]
        )
        assert (
            "options.closurePass = flags.process_closure_primitives;"
            in sample["fixed_code"]
        )
        assert "if (flags.process_closure_primitives) {" in sample["buggy_code"]
        assert not "if (flags.process_closure_primitives) {" in sample["fixed_code"]

        # Assert that the prompt is properly constructed
        assert (
            sample["prompt"]
            .strip()
            .startswith("protected CompilerOptions createOptions() {")
        )
        assert sample["prompt"].count("<|mask:") == 2
        assert sample["prompt"].count("<|mask:0|>") == 1
        assert sample["prompt"].count("<|mask:1|>") == 1

    # def test_lang_10(self):
    #     bug = TestClozeSamplesIncoder.DEFECTS4J.get_bug("Lang-10")
    #     assert bug is not None

    #     sample = generate_sample(
    #         bug=bug,
    #         prompt_strategy=TestClozeSamplesIncoder.PROMPT_STRATEGY,
    #         model_name=TestClozeSamplesIncoder.MODEL_NAME,
    #     )

    #     # Assert we are dealing with the correct bug and strategy
    #     assert sample["identifier"] == "Lang-10"
    #     assert sample["prompt_strategy"] == "zero-shot-cloze"

    #     print(sample["buggy_code"])
    #     print(sample["fixed_code"])

    #     print(sample["prompt"])

    #     # TODO: Adapt to Lang-10
    #     # # Assert that the buggy code and fixed code are properly separated
    #     # assert not "if(numDecimals <= 7){" in sample["buggy_code"]
    #     # assert "if(numDecimals <= 7){" in sample["fixed_code"]

    #     # # Assert that the prompt is properly constructed
    #     # assert (
    #     #     sample["prompt"]
    #     #     .strip()
    #     #     .startswith(
    #     #         "public static Number createNumber(final String str) throws NumberFormatException"
    #     #     )
    #     # )
    #     # assert sample["prompt"].count("<|mask:") == 4
    #     # assert sample["prompt"].count("<|mask:0|>") == 1
    #     # assert sample["prompt"].count("<|mask:1|>") == 1
    #     # assert sample["prompt"].count("<|mask:2|>") == 1
    #     # assert sample["prompt"].count("<|mask:3|>") == 1

    def test_chart_23(self):
        bug = TestClozeSamplesIncoder.DEFECTS4J.get_bug("Chart-23")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesIncoder.PROMPT_STRATEGY,
            model_name=TestClozeSamplesIncoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Chart-23"
        assert sample["prompt_strategy"] == "zero-shot-cloze"

        # Assert that the buggy code and fixed code are properly separated
        assert sample["buggy_code"] is None
        assert "public boolean equals(Object obj) {" in sample["fixed_code"]

        # Assert that the prompt is properly constructed
        assert (
            sample["prompt"]
            .strip()
            .startswith(
                "<|mask:0|>"
            )
        )
        assert sample["prompt"].count("<|mask:") == 1
        assert sample["prompt"].count("<|mask:0|>") == 1