from evaluate_patches import evaluate_candidate
from generate_samples import generate_sample
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.benchmarks.benchmark import Benchmark

import pytest
import os


class TestEvaluatePatchesReplaceDefects4J:
    DEFECTS4J: Benchmark
    PROMPT_STRATEGY: str = "zero-shot-cloze"
    MODEL_NAME: str = "incoder"
    EVALUATE_STRATEGY: str = "replace"

    @classmethod
    def setup_class(cls):
        TestEvaluatePatchesReplaceDefects4J.DEFECTS4J = get_benchmark("defects4j")
        assert TestEvaluatePatchesReplaceDefects4J.DEFECTS4J is not None
        TestEvaluatePatchesReplaceDefects4J.DEFECTS4J.initialize()

    @classmethod
    def get_exact_match_sample(cls):
        bug = TestEvaluatePatchesReplaceDefects4J.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestEvaluatePatchesReplaceDefects4J.PROMPT_STRATEGY,
            model_name=TestEvaluatePatchesReplaceDefects4J.MODEL_NAME,
        )
        sample["generation"] = [sample["fixed_code"] + "\n// comment"]
        return bug, sample

    @classmethod
    def get_ast_match_sample(cls):
        bug = TestEvaluatePatchesReplaceDefects4J.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestEvaluatePatchesReplaceDefects4J.PROMPT_STRATEGY,
            model_name=TestEvaluatePatchesReplaceDefects4J.MODEL_NAME,
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
    def get_plausible_sample(cls):
        bug = TestEvaluatePatchesReplaceDefects4J.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestEvaluatePatchesReplaceDefects4J.PROMPT_STRATEGY,
            model_name=TestEvaluatePatchesReplaceDefects4J.MODEL_NAME,
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
        } else {
            int a = 0;
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
        bug = TestEvaluatePatchesReplaceDefects4J.DEFECTS4J.get_bug("Chart-1")
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestEvaluatePatchesReplaceDefects4J.PROMPT_STRATEGY,
            model_name=TestEvaluatePatchesReplaceDefects4J.MODEL_NAME,
        )
        sample["generation"] = [sample["buggy_code"]]
        return bug, sample

    def test_exact_match_patch(self):
        bug, sample = TestEvaluatePatchesReplaceDefects4J.get_exact_match_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            strategy=TestEvaluatePatchesReplaceDefects4J.EVALUATE_STRATEGY,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == True
        assert sample["evaluation"][0]["exact_match"] == True
        assert sample["evaluation"][0]["ast_match"] == True

    def test_ast_match_patch(self):
        bug, sample = TestEvaluatePatchesReplaceDefects4J.get_ast_match_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            strategy=TestEvaluatePatchesReplaceDefects4J.EVALUATE_STRATEGY,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == True
        assert sample["evaluation"][0]["ast_match"] == True
        assert sample["evaluation"][0]["exact_match"] == False

    def test_incorrect_patch(self):
        bug, sample = TestEvaluatePatchesReplaceDefects4J.get_incorrect_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            strategy=TestEvaluatePatchesReplaceDefects4J.EVALUATE_STRATEGY,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == False
        assert sample["evaluation"][0]["exact_match"] == False
        assert sample["evaluation"][0]["ast_match"] == False

    def test_plausible_patch(self):
        bug, sample = TestEvaluatePatchesReplaceDefects4J.get_plausible_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            strategy=TestEvaluatePatchesReplaceDefects4J.EVALUATE_STRATEGY,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == True
        assert sample["evaluation"][0]["exact_match"] == False
        assert sample["evaluation"][0]["ast_match"] == False


@pytest.mark.skipif(
    os.environ.get("CI") is not None,
    reason="This test requires completing GitBug-Java's setup, which is too heavy for CI.",
)
class TestEvaluatePatchesReplaceGitBugJava:
    GITBUGJAVA: Benchmark
    PROMPT_STRATEGY: str = "zero-shot-cloze"
    MODEL_NAME: str = "incoder"
    EVALUATE_STRATEGY: str = "replace"

    @classmethod
    def setup_class(cls):
        TestEvaluatePatchesReplaceGitBugJava.GITBUGJAVA = get_benchmark("gitbugjava")
        assert TestEvaluatePatchesReplaceGitBugJava.GITBUGJAVA is not None
        TestEvaluatePatchesReplaceGitBugJava.GITBUGJAVA.initialize()

    @classmethod
    def get_exact_match_sample(cls):
        bug = TestEvaluatePatchesReplaceGitBugJava.GITBUGJAVA.get_bug(
            "beanshell-beanshell-f345606a29bd"
        )
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestEvaluatePatchesReplaceGitBugJava.PROMPT_STRATEGY,
            model_name=TestEvaluatePatchesReplaceGitBugJava.MODEL_NAME,
        )
        sample["generation"] = [sample["fixed_code"] + "\n// comment"]
        return bug, sample

    @classmethod
    def get_ast_match_sample(cls):
        bug = TestEvaluatePatchesReplaceGitBugJava.GITBUGJAVA.get_bug(
            "beanshell-beanshell-f345606a29bd"
        )
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestEvaluatePatchesReplaceGitBugJava.PROMPT_STRATEGY,
            model_name=TestEvaluatePatchesReplaceGitBugJava.MODEL_NAME,
        )
        sample["generation"] = [
            """    public static Object arbitraryObjectsBinaryOperation(
        Object lhs, Object rhs, int kind)
        throws UtilEvalError
    {
        if ( kind == EQ )
            return (lhs == rhs) ? Primitive.TRUE : Primitive.FALSE;
        if ( kind == NE )
            return (lhs != rhs) ? Primitive.TRUE : Primitive.FALSE;

        if ( lhs == Primitive.VOID || rhs == Primitive.VOID )
            throw new UtilEvalError(
                "illegal use of undefined variable, class, or"
                    + " 'void' literal");

        if (kind == SPACESHIP) {
            int comp = 0; // used to ensure only -1, 0, and 1 is returned.
            if (lhs instanceof Comparable || rhs instanceof Comparable)
                comp = Comparator.nullsFirst( // nullsFirst Comparable Comparator
                    Comparator.<Comparable<Object>>naturalOrder())
                        .compare((Comparable<Object>)Primitive.unwrap(lhs),
                            (Comparable<Object>)Primitive.unwrap(rhs));
            else
                comp = Comparator.nullsFirst( // nullsFirst toString Comparator
                    Comparator.comparing(Object::toString))
                    .compare(Primitive.unwrap(lhs), Primitive.unwrap(rhs));
            return Primitive.wrap(comp < 0 ? -1 : comp > 0 ? 1 : 0, Integer.TYPE);
        }

        if ( kind == PLUS ) {
            // String concatenation operation
            if ( lhs instanceof String || rhs instanceof String )
                return BSHLiteral.internStrings
                    ? (String.valueOf((Object) lhs) + String.valueOf((Object) rhs))
                    .intern()
                    : String.valueOf((Object) lhs) + String.valueOf((Object) rhs);
            // array concatenation operation
            if ( lhs.getClass().isArray() && rhs instanceof List )
                rhs = ((List<?>) rhs).toArray();
            if ( lhs.getClass().isArray()
                    && rhs.getClass().isArray() )
                return BshArray.concat(lhs, rhs);
            // list concatenation operation
            if ( lhs instanceof List && rhs.getClass().isArray() )
                rhs = Types.castObject(rhs, List.class, Types.CAST);
            if ( lhs instanceof List && rhs instanceof List )
                return BshArray.concat(
                        (List<?>) lhs, (List<?>) rhs);
        }
        if ( kind == STAR ) {
            // array repeat operation
            if ( lhs.getClass().isArray() )
                return BshArray.repeat(lhs,
                        (int) Primitive.unwrap(rhs));
            if ( rhs.getClass().isArray() )
                return BshArray.repeat(rhs,
                        (int) Primitive.unwrap(lhs));
            // List repeat operation
            if ( lhs instanceof List )
                return BshArray.repeat((List<Object>) lhs,
                        (int) Primitive.unwrap(rhs));
            if ( rhs instanceof List )
                return BshArray.repeat((List<Object>) rhs,
                        (int) Primitive.unwrap(lhs));
        }

        if ( lhs instanceof String || rhs instanceof String )
            throw new UtilEvalError(
                "Use of non + operator with String" );
        if ( lhs.getClass().isArray() || rhs.getClass().isArray()
               || lhs instanceof List || rhs instanceof List)
            throw new UtilEvalError(
                "Use of invalid operator " + tokenImage[kind]
                    + " with array or List type" );
        if ( lhs == Primitive.NULL || rhs == Primitive.NULL )
            throw new UtilEvalError(
                "illegal use of null value or 'null' literal");

        throw new UtilEvalError("Operator: " + tokenImage[kind]
                    + " inappropriate for objects");
    }
"""
        ]
        return bug, sample

    @classmethod
    def get_plausible_sample(cls):
        bug = TestEvaluatePatchesReplaceGitBugJava.GITBUGJAVA.get_bug(
            "beanshell-beanshell-f345606a29bd"
        )
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestEvaluatePatchesReplaceGitBugJava.PROMPT_STRATEGY,
            model_name=TestEvaluatePatchesReplaceGitBugJava.MODEL_NAME,
        )
        sample["generation"] = [
            """    public static Object arbitraryObjectsBinaryOperation(
        Object lhs, Object rhs, int kind)
        throws UtilEvalError
    {
        if ( kind == EQ )
            return (lhs == rhs) ? Primitive.TRUE : Primitive.FALSE;
        if ( kind == NE )
            return (lhs != rhs) ? Primitive.TRUE : Primitive.FALSE;

        if ( lhs == Primitive.VOID || rhs == Primitive.VOID )
            throw new UtilEvalError(
                "illegal use of undefined variable, class, or"
                    + " 'void' literal");

        if (kind == SPACESHIP) {
            int comp = 0; // used to ensure only -1, 0, and 1 is returned.
            if (lhs instanceof Comparable || rhs instanceof Comparable)
                comp = Comparator.nullsFirst( // nullsFirst Comparable Comparator
                    Comparator.<Comparable<Object>>naturalOrder())
                        .compare((Comparable<Object>)Primitive.unwrap(lhs),
                            (Comparable<Object>)Primitive.unwrap(rhs));
            else
                comp = Comparator.nullsFirst( // nullsFirst toString Comparator
                    Comparator.comparing(Object::toString))
                    .compare(Primitive.unwrap(lhs), Primitive.unwrap(rhs));
            return Primitive.wrap(comp < 0 ? -1 : comp > 0 ? 1 : 0, Integer.TYPE);
        }

        if ( kind == PLUS ) {
            // String concatenation operation
            if ( lhs instanceof String || rhs instanceof String )
                return !BSHLiteral.internStrings
                    ? String.valueOf((Object) lhs) + String.valueOf((Object) rhs)
                    : (String.valueOf((Object) lhs) + String.valueOf((Object) rhs)).intern();
            // array concatenation operation
            if ( lhs.getClass().isArray() && rhs instanceof List )
                rhs = ((List<?>) rhs).toArray();
            if ( lhs.getClass().isArray()
                    && rhs.getClass().isArray() )
                return BshArray.concat(lhs, rhs);
            // list concatenation operation
            if ( lhs instanceof List && rhs.getClass().isArray() )
                rhs = Types.castObject(rhs, List.class, Types.CAST);
            if ( lhs instanceof List && rhs instanceof List )
                return BshArray.concat(
                        (List<?>) lhs, (List<?>) rhs);
        }
        if ( kind == STAR ) {
            // array repeat operation
            if ( lhs.getClass().isArray() )
                return BshArray.repeat(lhs,
                        (int) Primitive.unwrap(rhs));
            if ( rhs.getClass().isArray() )
                return BshArray.repeat(rhs,
                        (int) Primitive.unwrap(lhs));
            // List repeat operation
            if ( lhs instanceof List )
                return BshArray.repeat((List<Object>) lhs,
                        (int) Primitive.unwrap(rhs));
            if ( rhs instanceof List )
                return BshArray.repeat((List<Object>) rhs,
                        (int) Primitive.unwrap(lhs));
        }

        if ( lhs instanceof String || rhs instanceof String )
            throw new UtilEvalError(
                "Use of non + operator with String" );
        if ( lhs.getClass().isArray() || rhs.getClass().isArray()
               || lhs instanceof List || rhs instanceof List)
            throw new UtilEvalError(
                "Use of invalid operator " + tokenImage[kind]
                    + " with array or List type" );
        if ( lhs == Primitive.NULL || rhs == Primitive.NULL )
            throw new UtilEvalError(
                "illegal use of null value or 'null' literal");

        throw new UtilEvalError("Operator: " + tokenImage[kind]
                    + " inappropriate for objects");
    }
"""
        ]
        return bug, sample

    @classmethod
    def get_incorrect_sample(cls):
        bug = TestEvaluatePatchesReplaceGitBugJava.GITBUGJAVA.get_bug(
            "beanshell-beanshell-f345606a29bd"
        )
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestEvaluatePatchesReplaceGitBugJava.PROMPT_STRATEGY,
            model_name=TestEvaluatePatchesReplaceGitBugJava.MODEL_NAME,
        )
        sample["generation"] = [sample["buggy_code"]]
        return bug, sample

    def test_exact_match_patch(self):
        bug, sample = TestEvaluatePatchesReplaceGitBugJava.get_exact_match_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            strategy=TestEvaluatePatchesReplaceGitBugJava.EVALUATE_STRATEGY,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == True
        assert sample["evaluation"][0]["test"] == True
        assert sample["evaluation"][0]["exact_match"] == True
        assert sample["evaluation"][0]["ast_match"] == True

    def test_ast_match_patch(self):
        bug, sample = TestEvaluatePatchesReplaceGitBugJava.get_ast_match_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            strategy=TestEvaluatePatchesReplaceGitBugJava.EVALUATE_STRATEGY,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == None
        assert sample["evaluation"][0]["test"] == True
        assert sample["evaluation"][0]["ast_match"] == True
        assert sample["evaluation"][0]["exact_match"] == False

    def test_incorrect_patch(self):
        bug, sample = TestEvaluatePatchesReplaceGitBugJava.get_incorrect_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            strategy=TestEvaluatePatchesReplaceGitBugJava.EVALUATE_STRATEGY,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == None
        assert sample["evaluation"][0]["test"] == False
        assert sample["evaluation"][0]["exact_match"] == False
        assert sample["evaluation"][0]["ast_match"] == False

    def test_plausible_patch(self):
        bug, sample = TestEvaluatePatchesReplaceGitBugJava.get_plausible_sample()

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            strategy=TestEvaluatePatchesReplaceGitBugJava.EVALUATE_STRATEGY,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == None
        assert sample["evaluation"][0]["test"] == True
        assert sample["evaluation"][0]["exact_match"] == False
        assert sample["evaluation"][0]["ast_match"] == False

    def test_mthmulders_mcs_eff905bef8d8(self):
        """This test is for a specific bug in GitBug-Java that we faced an issue in locating the buggy code of during evaluation."""
        bug = TestEvaluatePatchesReplaceGitBugJava.GITBUGJAVA.get_bug(
            "mthmulders-mcs-eff905bef8d8"
        )
        assert bug is not None

        sample = generate_sample(
            bug=bug,
            prompt_strategy=TestEvaluatePatchesReplaceGitBugJava.PROMPT_STRATEGY,
            model_name=TestEvaluatePatchesReplaceGitBugJava.MODEL_NAME,
        )

        sample["generation"] = [
            """    private void printRow(final Help.TextTable table, final SearchResponse.Response.Doc doc) {
        var lastUpdated = DATE_TIME_FORMATTER.format(
                Instant.ofEpochMilli(doc.timestamp()).atZone(ZoneId.systemDefault())
        );

        table.addRowValues(
            doc.id() + ":" + doc.latestVersion(), lastUpdated
        );
    }
"""
        ]

        sample = evaluate_candidate(
            bug=bug,
            sample=sample,
            strategy=TestEvaluatePatchesReplaceGitBugJava.EVALUATE_STRATEGY,
        )

        assert sample["evaluation"] is not None
        assert len(sample["evaluation"]) == 1

        assert sample["evaluation"][0]["compile"] == None
        assert sample["evaluation"][0]["test"] == True
        assert sample["evaluation"][0]["ast_match"] == True
        assert sample["evaluation"][0]["exact_match"] == False
