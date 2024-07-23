from generate_samples import generate_sample
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.benchmarks.benchmark import Benchmark


class TestFillInTheMiddleSamplesStarCoder:
    DEFECTS4J: Benchmark
    PROMPT_STRATEGY: str = "fill-in-the-middle"
    MODEL_NAME: str = "starcoder"

    @classmethod
    def setup_class(cls):
        TestFillInTheMiddleSamplesStarCoder.DEFECTS4J = get_benchmark("defects4j")
        assert TestFillInTheMiddleSamplesStarCoder.DEFECTS4J is not None
        TestFillInTheMiddleSamplesStarCoder.DEFECTS4J.initialize()

    def test_closure_46(self):
        bug = TestFillInTheMiddleSamplesStarCoder.DEFECTS4J.get_bug("Closure-46")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestFillInTheMiddleSamplesStarCoder.PROMPT_STRATEGY,
            model_name=TestFillInTheMiddleSamplesStarCoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Closure-46"
        assert sample["prompt_strategy"] == "fill-in-the-middle"

        # Assert that the buggy code and fixed code are properly separated
        assert "public JSType getLeastSupertype(JSType that) {" in sample["buggy_code"]
        assert sample["fixed_code"] == ""

    def test_closure_115(self):
        bug = TestFillInTheMiddleSamplesStarCoder.DEFECTS4J.get_bug("Closure-115")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestFillInTheMiddleSamplesStarCoder.PROMPT_STRATEGY,
            model_name=TestFillInTheMiddleSamplesStarCoder.MODEL_NAME,
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
                "<fim_prefix>  /**\n   * Determines whether a function can be inlined at a particular call site."
            )
        )
        assert sample["prompt"].endswith("<fim_middle>")
        assert sample["prompt"].count("<fim_prefix>") == 1
        assert sample["prompt"].count("<fim_middle>") == 1
        assert sample["prompt"].count("<fim_suffix>") == 1

    def test_closure_4(self):
        bug = TestFillInTheMiddleSamplesStarCoder.DEFECTS4J.get_bug("Closure-4")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestFillInTheMiddleSamplesStarCoder.PROMPT_STRATEGY,
            model_name=TestFillInTheMiddleSamplesStarCoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Closure-4"
        assert sample["prompt_strategy"] == "fill-in-the-middle"

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
                "<fim_prefix>  /**\n   * Resolve the referenced type within the enclosing scope.\n   */"
            )
        )
        assert sample["prompt"].endswith("<fim_middle>")
        assert sample["prompt"].count("<fim_prefix>") == 1
        assert sample["prompt"].count("<fim_middle>") == 1
        assert sample["prompt"].count("<fim_suffix>") == 1

    def test_chart_4(self):
        bug = TestFillInTheMiddleSamplesStarCoder.DEFECTS4J.get_bug("Chart-4")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestFillInTheMiddleSamplesStarCoder.PROMPT_STRATEGY,
            model_name=TestFillInTheMiddleSamplesStarCoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Chart-4"
        assert sample["prompt_strategy"] == "fill-in-the-middle"

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
            .startswith(
                "<fim_prefix>    /**\n     * Returns the range for the specified axis."
            )
        )
        assert sample["prompt"].endswith("<fim_middle>")
        assert sample["prompt"].count("<fim_prefix>") == 1
        assert sample["prompt"].count("<fim_middle>") == 1
        assert sample["prompt"].count("<fim_suffix>") == 1

    def test_chart_2(self):
        bug = TestFillInTheMiddleSamplesStarCoder.DEFECTS4J.get_bug("Chart-2")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestFillInTheMiddleSamplesStarCoder.PROMPT_STRATEGY,
            model_name=TestFillInTheMiddleSamplesStarCoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Chart-2"
        assert sample["prompt_strategy"] == "fill-in-the-middle"

        # Assert that the prompt was not generated
        assert sample["prompt"] is None

    def test_math_99(self):
        bug = TestFillInTheMiddleSamplesStarCoder.DEFECTS4J.get_bug("Math-99")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestFillInTheMiddleSamplesStarCoder.PROMPT_STRATEGY,
            model_name=TestFillInTheMiddleSamplesStarCoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Math-99"
        assert sample["prompt_strategy"] == "fill-in-the-middle"

        # Assert that the prompt was not generated
        assert sample["prompt"] is None

    def test_chart_18(self):
        bug = TestFillInTheMiddleSamplesStarCoder.DEFECTS4J.get_bug("Chart-18")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestFillInTheMiddleSamplesStarCoder.PROMPT_STRATEGY,
            model_name=TestFillInTheMiddleSamplesStarCoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Chart-18"
        assert sample["prompt_strategy"] == "fill-in-the-middle"

        # Assert that the prompt was not generated
        assert sample["prompt"] is None

    def test_closure_11(self):
        bug = TestFillInTheMiddleSamplesStarCoder.DEFECTS4J.get_bug("Closure-11")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestFillInTheMiddleSamplesStarCoder.PROMPT_STRATEGY,
            model_name=TestFillInTheMiddleSamplesStarCoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Closure-11"
        assert sample["prompt_strategy"] == "fill-in-the-middle"

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
        assert sample["prompt"].startswith(
            "<fim_prefix>  /**\n   * Visits a GETPROP node."
        )
        assert sample["prompt"].endswith("<fim_middle>")
        assert sample["prompt"].count("<fim_prefix>") == 1
        assert sample["prompt"].count("<fim_middle>") == 1
        assert sample["prompt"].count("<fim_suffix>") == 1

    def test_closure_5(self):
        bug = TestFillInTheMiddleSamplesStarCoder.DEFECTS4J.get_bug("Closure-5")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestFillInTheMiddleSamplesStarCoder.PROMPT_STRATEGY,
            model_name=TestFillInTheMiddleSamplesStarCoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Closure-5"
        assert sample["prompt_strategy"] == "fill-in-the-middle"

        # Assert that the buggy code and fixed code are properly separated
        assert "if (gramps.isDelProp()) {" not in sample["buggy_code"]
        assert "if (gramps.isDelProp()) {" in sample["fixed_code"]

        # Assert that the prompt is properly constructed
        assert sample["prompt"].startswith(
            "<fim_prefix>    /**\n     * Counts the number of direct (full) references to an object."
        )
        assert sample["prompt"].endswith("<fim_middle>")
        assert sample["prompt"].count("<fim_prefix>") == 1
        assert sample["prompt"].count("<fim_middle>") == 1
        assert sample["prompt"].count("<fim_suffix>") == 1

    def test_chart_6(self):
        bug = TestFillInTheMiddleSamplesStarCoder.DEFECTS4J.get_bug("Chart-6")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestFillInTheMiddleSamplesStarCoder.PROMPT_STRATEGY,
            model_name=TestFillInTheMiddleSamplesStarCoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Chart-6"
        assert sample["prompt_strategy"] == "fill-in-the-middle"

        # Assert that the buggy code and fixed code are properly separated
        assert "return super.equals(obj);" in sample["buggy_code"]
        assert "return super.equals(obj);" not in sample["fixed_code"]
        assert "ShapeList that = (ShapeList) obj;" not in sample["buggy_code"]
        assert "ShapeList that = (ShapeList) obj;" in sample["fixed_code"]

        # Assert that the prompt is properly constructed
        assert sample["prompt"].startswith(
            "<fim_prefix>    /**\n     * Tests the list for equality with another object (typically also a list)."
        )
        assert sample["prompt"].endswith("<fim_middle>")
        assert sample["prompt"].count("<fim_prefix>") == 1
        assert sample["prompt"].count("<fim_middle>") == 1
        assert sample["prompt"].count("<fim_suffix>") == 1

    def test_lang_3(self):
        bug = TestFillInTheMiddleSamplesStarCoder.DEFECTS4J.get_bug("Lang-3")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestFillInTheMiddleSamplesStarCoder.PROMPT_STRATEGY,
            model_name=TestFillInTheMiddleSamplesStarCoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Lang-3"
        assert sample["prompt_strategy"] == "fill-in-the-middle"

        # Assert that the buggy code and fixed code are properly separated
        assert "if(numDecimals <= 7){" not in sample["buggy_code"]
        assert "if(numDecimals <= 7){" in sample["fixed_code"]

        # Assert that the prompt is properly constructed
        assert (
            sample["prompt"]
            .strip()
            .startswith(
                "<fim_prefix>    /**\n     * <p>Turns a string value into a java.lang.Number.</p>\n     *"
            )
        )
        assert sample["prompt"].endswith("<fim_middle>")
        assert sample["prompt"].count("<fim_prefix>") == 1
        assert sample["prompt"].count("<fim_middle>") == 1
        assert sample["prompt"].count("<fim_suffix>") == 1

    def test_closure_101(self):
        bug = TestFillInTheMiddleSamplesStarCoder.DEFECTS4J.get_bug("Closure-101")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestFillInTheMiddleSamplesStarCoder.PROMPT_STRATEGY,
            model_name=TestFillInTheMiddleSamplesStarCoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Closure-101"
        assert sample["prompt_strategy"] == "fill-in-the-middle"

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
            .startswith(
                "<fim_prefix>  @Override\n  protected CompilerOptions createOptions() {"
            )
        )
        assert sample["prompt"].endswith("<fim_middle>")
        assert sample["prompt"].count("<fim_prefix>") == 1
        assert sample["prompt"].count("<fim_middle>") == 1
        assert sample["prompt"].count("<fim_suffix>") == 1

    def test_lang_10(self):
        bug = TestFillInTheMiddleSamplesStarCoder.DEFECTS4J.get_bug("Lang-10")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestFillInTheMiddleSamplesStarCoder.PROMPT_STRATEGY,
            model_name=TestFillInTheMiddleSamplesStarCoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Lang-10"
        assert sample["prompt_strategy"] == "fill-in-the-middle"

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
                "<fim_prefix>    /**\n     * Escape constant fields into regular expression"
            )
        )
        assert sample["prompt"].endswith("<fim_middle>")
        assert sample["prompt"].count("<fim_prefix>") == 1
        assert sample["prompt"].count("<fim_middle>") == 1
        assert sample["prompt"].count("<fim_suffix>") == 1

    def test_chart_7(self):
        # This is a special case that requires latin-1 encoding
        bug = TestFillInTheMiddleSamplesStarCoder.DEFECTS4J.get_bug("Chart-7")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestFillInTheMiddleSamplesStarCoder.PROMPT_STRATEGY,
            model_name=TestFillInTheMiddleSamplesStarCoder.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Chart-7"
        assert sample["prompt_strategy"] == "fill-in-the-middle"

        # Assert that the prompt is properly constructed
        assert (
            sample["prompt"]
            .strip()
            .startswith(
                "<fim_prefix>    /**\n     * Update the index values for the maximum and minimum bounds."
            )
        )
        assert sample["prompt"].endswith("<fim_middle>")
        assert sample["prompt"].count("<fim_prefix>") == 1
        assert sample["prompt"].count("<fim_middle>") == 1
        assert sample["prompt"].count("<fim_suffix>") == 1
