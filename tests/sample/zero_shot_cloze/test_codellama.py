from generate_samples import generate_sample
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.benchmarks.benchmark import Benchmark


class TestClozeSamplesCodeLLaMA:
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
    MODEL_NAME: str = "codellama"

    @classmethod
    def setup_class(cls):
        TestClozeSamplesCodeLLaMA.DEFECTS4J = get_benchmark("defects4j")
        assert TestClozeSamplesCodeLLaMA.DEFECTS4J is not None
        TestClozeSamplesCodeLLaMA.DEFECTS4J.initialize()

    def test_closure_46(self):
        bug = TestClozeSamplesCodeLLaMA.DEFECTS4J.get_bug("Closure-46")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesCodeLLaMA.PROMPT_STRATEGY,
            model_name=TestClozeSamplesCodeLLaMA.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Closure-46"
        assert sample["prompt_strategy"] == "zero-shot-cloze"

        # Not supported since it changes the annotation too (outside the method declaration)
        assert sample["prompt"] is None

    def test_closure_115(self):
        bug = TestClozeSamplesCodeLLaMA.DEFECTS4J.get_bug("Closure-115")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesCodeLLaMA.PROMPT_STRATEGY,
            model_name=TestClozeSamplesCodeLLaMA.MODEL_NAME,
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
        assert sample["prompt"].count("<FILL_ME>") == 1

    def test_closure_4(self):
        bug = TestClozeSamplesCodeLLaMA.DEFECTS4J.get_bug("Closure-4")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesCodeLLaMA.PROMPT_STRATEGY,
            model_name=TestClozeSamplesCodeLLaMA.MODEL_NAME,
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
                "JSType resolveInternal(ErrorReporter t, StaticScope<JSType> enclosing) {"
            )
        )
        assert sample["prompt"].count("<FILL_ME>") == 1

    def test_chart_4(self):
        bug = TestClozeSamplesCodeLLaMA.DEFECTS4J.get_bug("Chart-4")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesCodeLLaMA.PROMPT_STRATEGY,
            model_name=TestClozeSamplesCodeLLaMA.MODEL_NAME,
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
        assert sample["prompt"].count("<FILL_ME>") == 1

    def test_chart_2(self):
        bug = TestClozeSamplesCodeLLaMA.DEFECTS4J.get_bug("Chart-2")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesCodeLLaMA.PROMPT_STRATEGY,
            model_name=TestClozeSamplesCodeLLaMA.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Chart-2"
        assert sample["prompt_strategy"] == "zero-shot-cloze"

        # Assert that the prompt was not generated
        assert sample["prompt"] is None

    def test_math_99(self):
        bug = TestClozeSamplesCodeLLaMA.DEFECTS4J.get_bug("Math-99")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesCodeLLaMA.PROMPT_STRATEGY,
            model_name=TestClozeSamplesCodeLLaMA.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Math-99"
        assert sample["prompt_strategy"] == "zero-shot-cloze"

        # Assert that the prompt was not generated
        assert sample["prompt"] is None

    def test_chart_18(self):
        bug = TestClozeSamplesCodeLLaMA.DEFECTS4J.get_bug("Chart-18")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesCodeLLaMA.PROMPT_STRATEGY,
            model_name=TestClozeSamplesCodeLLaMA.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Chart-18"
        assert sample["prompt_strategy"] == "zero-shot-cloze"

        # Assert that the prompt was not generated
        assert sample["prompt"] is None

    def test_closure_11(self):
        bug = TestClozeSamplesCodeLLaMA.DEFECTS4J.get_bug("Closure-11")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesCodeLLaMA.PROMPT_STRATEGY,
            model_name=TestClozeSamplesCodeLLaMA.MODEL_NAME,
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
        assert sample["prompt"].count("<FILL_ME>") == 1

    def test_chart_1_keep_buggy_code(self):
        bug = TestClozeSamplesCodeLLaMA.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesCodeLLaMA.PROMPT_STRATEGY,
            model_name=TestClozeSamplesCodeLLaMA.MODEL_NAME,
            keep_buggy_code=True,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Chart-1"
        assert sample["prompt_strategy"] == "zero-shot-cloze"

        assert (
            sample["prompt"]
            == """    public LegendItemCollection getLegendItems() {
        LegendItemCollection result = new LegendItemCollection();
        if (this.plot == null) {
            return result;
        }
        int index = this.plot.getIndexOf(this);
        CategoryDataset dataset = this.plot.getDataset(index);
// buggy code
//        if (dataset != null) {
<FILL_ME>
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
        )

    def test_chart_5_keep_buggy_code(self):
        bug = TestClozeSamplesCodeLLaMA.DEFECTS4J.get_bug("Chart-5")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesCodeLLaMA.PROMPT_STRATEGY,
            model_name=TestClozeSamplesCodeLLaMA.MODEL_NAME,
            keep_buggy_code=True,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Chart-5"
        assert sample["prompt_strategy"] == "zero-shot-cloze"

        assert (
            sample["prompt"]
            == """    public XYDataItem addOrUpdate(Number x, Number y) {
        if (x == null) {
            throw new IllegalArgumentException("Null 'x' argument.");
// buggy code
//        }
//
//        // if we get to here, we know that duplicate X values are not permitted
//        XYDataItem overwritten = null;
//        int index = indexOf(x);
//        if (index >= 0 && !this.allowDuplicateXValues) {
<FILL_ME>
            XYDataItem existing = (XYDataItem) this.data.get(index);
            try {
                overwritten = (XYDataItem) existing.clone();
            }
            catch (CloneNotSupportedException e) {
                throw new SeriesException("Couldn't clone XYDataItem!");
            }
            existing.setY(y);
        }
        else {
            // if the series is sorted, the negative index is a result from
            // Collections.binarySearch() and tells us where to insert the
            // new item...otherwise it will be just -1 and we should just
            // append the value to the list...
            if (this.autoSort) {
                this.data.add(-index - 1, new XYDataItem(x, y));
            }
            else {
                this.data.add(new XYDataItem(x, y));
            }
            // check if this addition will exceed the maximum item count...
            if (getItemCount() > this.maximumItemCount) {
                this.data.remove(0);
            }
        }
        fireSeriesChanged();
        return overwritten;
    }
"""
        )

    def test_closure_11_keep_buggy_code(self):
        bug = TestClozeSamplesCodeLLaMA.DEFECTS4J.get_bug("Closure-11")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesCodeLLaMA.PROMPT_STRATEGY,
            model_name=TestClozeSamplesCodeLLaMA.MODEL_NAME,
            keep_buggy_code=True,
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
        assert sample["prompt"].count("<FILL_ME>") == 1
        assert "// buggy code" in sample["prompt"]
        assert (
            "} else if (n.getJSType() != null && parent.isAssign()) {"
            in sample["prompt"]
        )

    def test_closure_5(self):
        bug = TestClozeSamplesCodeLLaMA.DEFECTS4J.get_bug("Closure-5")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesCodeLLaMA.PROMPT_STRATEGY,
            model_name=TestClozeSamplesCodeLLaMA.MODEL_NAME,
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
        assert sample["prompt"].count("<FILL_ME>") == 1

    def test_chart_6(self):
        bug = TestClozeSamplesCodeLLaMA.DEFECTS4J.get_bug("Chart-6")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesCodeLLaMA.PROMPT_STRATEGY,
            model_name=TestClozeSamplesCodeLLaMA.MODEL_NAME,
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
        assert sample["prompt"].count("<FILL_ME>") == 1

    def test_lang_3(self):
        bug = TestClozeSamplesCodeLLaMA.DEFECTS4J.get_bug("Lang-3")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesCodeLLaMA.PROMPT_STRATEGY,
            model_name=TestClozeSamplesCodeLLaMA.MODEL_NAME,
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
        assert sample["prompt"].count("<FILL_ME>") == 1

    def test_closure_101(self):
        bug = TestClozeSamplesCodeLLaMA.DEFECTS4J.get_bug("Closure-101")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesCodeLLaMA.PROMPT_STRATEGY,
            model_name=TestClozeSamplesCodeLLaMA.MODEL_NAME,
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
        assert sample["prompt"].count("<FILL_ME>") == 1

    def test_lang_10(self):
        bug = TestClozeSamplesCodeLLaMA.DEFECTS4J.get_bug("Lang-10")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesCodeLLaMA.PROMPT_STRATEGY,
            model_name=TestClozeSamplesCodeLLaMA.MODEL_NAME,
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
        assert sample["prompt"].count("<FILL_ME>") == 1

    def test_chart_23(self):
        bug = TestClozeSamplesCodeLLaMA.DEFECTS4J.get_bug("Chart-23")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesCodeLLaMA.PROMPT_STRATEGY,
            model_name=TestClozeSamplesCodeLLaMA.MODEL_NAME,
        )

        # Assert we are dealing with the correct bug and strategy
        assert sample["identifier"] == "Chart-23"
        assert sample["prompt_strategy"] == "zero-shot-cloze"

        # Assert that the buggy code and fixed code are properly separated
        assert sample["buggy_code"] == ""
        assert "public boolean equals(Object obj) {" in sample["fixed_code"]

        # Assert that the prompt is properly constructed
        assert sample["prompt"].strip().startswith("<FILL_ME>")
        assert sample["prompt"].count("<FILL_ME>") == 1

    def test_chart_7(self):
        # This is a special case that requires latin-1 encoding
        bug = TestClozeSamplesCodeLLaMA.DEFECTS4J.get_bug("Chart-7")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestClozeSamplesCodeLLaMA.PROMPT_STRATEGY,
            model_name=TestClozeSamplesCodeLLaMA.MODEL_NAME,
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
        assert sample["prompt"].count("<FILL_ME>") == 1
