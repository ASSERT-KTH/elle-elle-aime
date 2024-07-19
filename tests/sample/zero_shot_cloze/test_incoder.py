from generate_samples import generate_sample
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.benchmarks.benchmark import Benchmark


class TestClozeSamplesIncoder:
    """
    We test the generation of cloze prompts for several types of bug fixes.
    We only generate samples for bugs that are single-function and single-file.
    The bugs in parenthesis are the examples tested in this class.

    We test the following types of bug fixes:
        - Addition only
            - Single-Hunk
                - N continuous lines (Closure-5)
                - N non-continous lines (Lang-3)
                - Whole function (Chart-23)
            - Multi-Hunk
                - N hunks of addition only (Chart-4)
        - Removal only
            - Single-Hunk
                - N continuous lines (Closure-11)
                - N non-continous lines (Lang-10)
                - Whole function (no example found, other than Closure-46 which also changes the annotation)
            - Multi-Hunk
                - N hunks of removal only (Closure-115)

        - Addition and removal
            - Single-Hunk
                - N continuous lines (Chart-6)
                - N non-continuous lines (Closure-101)
            - Multi-Hunk
                - N hunks of addition and removal (Closure-4)

    Unsupported bug types:
        - non single-function, single-file (Chart-2, Math-99, Closure-46 (special case, due to annotation change!))
        - non single-function, non single-file (Chart-18)
    """

    DEFECTS4J: Benchmark
    PROMPT_STRATEGY: str = "zero-shot-cloze"
    MODEL_NAME: str = "incoder"

    @classmethod
    def setup_class(cls):
        TestClozeSamplesIncoder.DEFECTS4J = get_benchmark("defects4j")
        assert TestClozeSamplesIncoder.DEFECTS4J is not None
        TestClozeSamplesIncoder.DEFECTS4J.initialize()

    def test_closure_46(self):
        bug = TestClozeSamplesIncoder.DEFECTS4J.get_bug("Closure-46")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesIncoder.PROMPT_STRATEGY,
            model_name=TestClozeSamplesIncoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Closure-46"
        assert sample["prompt_strategy"] == "zero-shot-cloze"

        # Assert that the buggy code and fixed code are properly separated
        assert "public JSType getLeastSupertype(JSType that) {" in sample["buggy_code"]
        assert sample["fixed_code"] == ""

    def test_closure_115(self):
        bug = TestClozeSamplesIncoder.DEFECTS4J.get_bug("Closure-115")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesIncoder.PROMPT_STRATEGY,
            model_name=TestClozeSamplesIncoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Closure-115"
        assert sample["prompt_strategy"] == "zero-shot-cloze"

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
            .startswith("private CanInlineResult canInlineReferenceDirectly(")
        )
        assert sample["prompt"].count("<|mask:") == 3
        assert sample["prompt"].count("<|mask:0|>") == 1
        assert sample["prompt"].count("<|mask:1|>") == 1
        assert sample["prompt"].count("<|mask:2|>") == 1

    def test_closure_4(self):
        bug = TestClozeSamplesIncoder.DEFECTS4J.get_bug("Closure-4")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesIncoder.PROMPT_STRATEGY,
            model_name=TestClozeSamplesIncoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Closure-4"
        assert sample["prompt_strategy"] == "zero-shot-cloze"

        # Assert that the buggy code and fixed code are properly separated
        assert "if (detectImplicitPrototypeCycle()) {" in sample["buggy_code"]
        assert "if (detectImplicitPrototypeCycle()) {" not in sample["fixed_code"]
        assert "if (detectInheritanceCycle()) {" not in sample["buggy_code"]
        assert "if (detectInheritanceCycle()) {" in sample["fixed_code"]

        # Assert that the prompt is properly constructed
        assert (
            sample["prompt"]
            .strip()
            .startswith(
                "@Override\n  JSType resolveInternal(ErrorReporter t, StaticScope<JSType> enclosing) {"
            )
        )
        assert sample["prompt"].count("<|mask:") == 3
        assert sample["prompt"].count("<|mask:0|>") == 1
        assert sample["prompt"].count("<|mask:1|>") == 1
        assert sample["prompt"].count("<|mask:2|>") == 1

    def test_chart_4(self):
        bug = TestClozeSamplesIncoder.DEFECTS4J.get_bug("Chart-4")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesIncoder.PROMPT_STRATEGY,
            model_name=TestClozeSamplesIncoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Chart-4"
        assert sample["prompt_strategy"] == "zero-shot-cloze"

        # Assert that the buggy code and fixed code are properly separated
        assert (
            """                if (r != null) {
                    Collection c = r.getAnnotations();"""
            not in sample["buggy_code"]
        )
        assert (
            """                if (r != null) {
                    Collection c = r.getAnnotations();"""
            in sample["fixed_code"]
        )

        # Assert that the prompt is properly constructed
        assert (
            sample["prompt"]
            .strip()
            .startswith("public Range getDataRange(ValueAxis axis) {")
        )
        assert sample["prompt"].count("<|mask:") == 3
        assert sample["prompt"].count("<|mask:0|>") == 1
        assert sample["prompt"].count("<|mask:1|>") == 1
        assert sample["prompt"].count("<|mask:2|>") == 1

    def test_chart_2(self):
        bug = TestClozeSamplesIncoder.DEFECTS4J.get_bug("Chart-2")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesIncoder.PROMPT_STRATEGY,
            model_name=TestClozeSamplesIncoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Chart-2"
        assert sample["prompt_strategy"] == "zero-shot-cloze"

        # Assert that the prompt was not generated
        assert sample["prompt"] is None

    def test_math_99(self):
        bug = TestClozeSamplesIncoder.DEFECTS4J.get_bug("Math-99")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesIncoder.PROMPT_STRATEGY,
            model_name=TestClozeSamplesIncoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Math-99"
        assert sample["prompt_strategy"] == "zero-shot-cloze"

        # Assert that the prompt was not generated
        assert sample["prompt"] is None

    def test_chart_18(self):
        bug = TestClozeSamplesIncoder.DEFECTS4J.get_bug("Chart-18")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesIncoder.PROMPT_STRATEGY,
            model_name=TestClozeSamplesIncoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Chart-18"
        assert sample["prompt_strategy"] == "zero-shot-cloze"

        # Assert that the prompt was not generated
        assert sample["prompt"] is None

    def test_closure_11(self):
        bug = TestClozeSamplesIncoder.DEFECTS4J.get_bug("Closure-11")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesIncoder.PROMPT_STRATEGY,
            model_name=TestClozeSamplesIncoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Closure-11"
        assert sample["prompt_strategy"] == "zero-shot-cloze"

        # Assert that the buggy code and fixed code are properly separated
        assert (
            "} else if (n.getJSType() != null && parent.isAssign()) {"
            in sample["buggy_code"]
        )
        assert (
            not "} else if (n.getJSType() != null && parent.isAssign()) {"
            in sample["fixed_code"]
        )

        # Assert that the prompt is properly constructed
        assert (
            sample["prompt"]
            .strip()
            .startswith(
                "private void visitGetProp(NodeTraversal t, Node n, Node parent) {"
            )
        )
        assert sample["prompt"].count("<|mask:") == 2
        assert sample["prompt"].count("<|mask:0|>") == 1
        assert sample["prompt"].count("<|mask:1|>") == 1

    def test_closure_5(self):
        bug = TestClozeSamplesIncoder.DEFECTS4J.get_bug("Closure-5")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesIncoder.PROMPT_STRATEGY,
            model_name=TestClozeSamplesIncoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Closure-5"
        assert sample["prompt_strategy"] == "zero-shot-cloze"

        # Assert that the buggy code and fixed code are properly separated
        assert "if (gramps.isDelProp()) {" not in sample["buggy_code"]
        assert "if (gramps.isDelProp()) {" in sample["fixed_code"]

        # Assert that the prompt is properly constructed
        assert (
            sample["prompt"]
            .strip()
            .startswith("private boolean isInlinableObject(List<Reference> refs) {")
        )
        assert sample["prompt"].count("<|mask:") == 2
        assert sample["prompt"].count("<|mask:0|>") == 1
        assert sample["prompt"].count("<|mask:1|>") == 1

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

        # Assert that the buggy code and fixed code are properly separated
        assert "return super.equals(obj);" in sample["buggy_code"]
        assert "return super.equals(obj);" not in sample["fixed_code"]
        assert "ShapeList that = (ShapeList) obj;" not in sample["buggy_code"]
        assert "ShapeList that = (ShapeList) obj;" in sample["fixed_code"]

        # Assert that the prompt is properly constructed
        assert (
            sample["prompt"].strip().startswith("public boolean equals(Object obj) {")
        )
        assert sample["prompt"].count("<|mask:") == 2
        assert sample["prompt"].count("<|mask:0|>") == 1
        assert sample["prompt"].count("<|mask:1|>") == 1

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
        assert "if(numDecimals <= 7){" not in sample["buggy_code"]
        assert "if(numDecimals <= 7){" in sample["fixed_code"]

        # Assert that the prompt is properly constructed
        assert (
            sample["prompt"]
            .strip()
            .startswith(
                "public static Number createNumber(final String str) throws NumberFormatException"
            )
        )
        assert sample["prompt"].count("<|mask:") == 5
        assert sample["prompt"].count("<|mask:0|>") == 1
        assert sample["prompt"].count("<|mask:1|>") == 1
        assert sample["prompt"].count("<|mask:2|>") == 1
        assert sample["prompt"].count("<|mask:3|>") == 1
        assert sample["prompt"].count("<|mask:4|>") == 1

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
        assert "if (flags.process_closure_primitives) {" not in sample["fixed_code"]

        # Assert that the prompt is properly constructed
        assert (
            sample["prompt"]
            .strip()
            .startswith("protected CompilerOptions createOptions() {")
        )
        assert sample["prompt"].count("<|mask:") == 2
        assert sample["prompt"].count("<|mask:0|>") == 1
        assert sample["prompt"].count("<|mask:1|>") == 1

    def test_lang_10(self):
        bug = TestClozeSamplesIncoder.DEFECTS4J.get_bug("Lang-10")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesIncoder.PROMPT_STRATEGY,
            model_name=TestClozeSamplesIncoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Lang-10"
        assert sample["prompt_strategy"] == "zero-shot-cloze"

        # Assert that the buggy code and fixed code are properly separated
        assert "if(Character.isWhitespace(c)) {" in sample["buggy_code"]
        assert "if(Character.isWhitespace(c)) {" not in sample["fixed_code"]
        assert "boolean wasWhite= false;" in sample["buggy_code"]
        assert "boolean wasWhite= false;" not in sample["fixed_code"]

        # Assert that the prompt is properly constructed
        assert (
            sample["prompt"]
            .strip()
            .startswith(
                "private static StringBuilder escapeRegex(StringBuilder regex, String value, boolean unquote) {"
            )
        )
        assert sample["prompt"].count("<|mask:") == 3
        assert sample["prompt"].count("<|mask:0|>") == 1
        assert sample["prompt"].count("<|mask:1|>") == 1
        assert sample["prompt"].count("<|mask:2|>") == 1

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
        assert sample["buggy_code"] == ""
        assert "public boolean equals(Object obj) {" in sample["fixed_code"]

        # Assert that the prompt is properly constructed
        assert sample["prompt"].strip().startswith("<|mask:0|>")
        assert sample["prompt"].count("<|mask:") == 2
        assert sample["prompt"].count("<|mask:0|>") == 1
        assert sample["prompt"].count("<|mask:1|>") == 1

    def test_chart_7(self):
        # This is a special case that requires latin-1 encoding
        bug = TestClozeSamplesIncoder.DEFECTS4J.get_bug("Chart-7")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesIncoder.PROMPT_STRATEGY,
            model_name=TestClozeSamplesIncoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Chart-7"
        assert sample["prompt_strategy"] == "zero-shot-cloze"

        # Assert that the prompt is properly constructed
        assert (
            sample["prompt"]
            .strip()
            .startswith("private void updateBounds(TimePeriod period, int index) {")
        )
        assert sample["prompt"].count("<|mask:") == 3
        assert sample["prompt"].count("<|mask:0|>") == 1
        assert sample["prompt"].count("<|mask:1|>") == 1
        assert sample["prompt"].count("<|mask:2|>") == 1
