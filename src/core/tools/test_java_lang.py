from core.tools.java_lang import *
from core.tools.patch import load_patch_file


def test_is_comment_line():
    assert is_comment_line("public static void main(String[] args) {") == False
    assert is_comment_line("return x;") == False
    assert is_comment_line("/* comment") == True
    assert is_comment_line("* comment") == True
    assert is_comment_line("*/") == True
    assert is_comment_line("// comment") == True


def test_clean_code():
    lines = ["public static void main(String[] args) {    ", "return x;    ",
             "", "}    "]
    result = clean_code(lines)
    assert clean_code(
        lines) == "public static void main(String[] args) {\nreturn x;\n}"


def test_load_ast_node():
    file_path = "src/fixtures/Defects4J_Closure_01_fixed.source"
    expect_nodes = [
        JavaAstNode(name='RemoveUnusedVars',
                    type='ClassDeclaration', start_pos=69, end_pos=998),
        JavaAstNode(name='RemoveUnusedVars',
                    type='ConstructorDeclaration', start_pos=123, end_pos=133),
        JavaAstNode(name='process', type='MethodDeclaration',
                    start_pos=140, end_pos=150),
        JavaAstNode(name='process', type='MethodDeclaration',
                    start_pos=153, end_pos=163),
        JavaAstNode(name='traverseAndRemoveUnusedReferences',
                    type='MethodDeclaration', start_pos=168, end_pos=181),
        JavaAstNode(name='traverseNode', type='MethodDeclaration',
                    start_pos=192, end_pos=305),
        JavaAstNode(name='isRemovableVar', type='MethodDeclaration',
                    start_pos=307, end_pos=324),
        JavaAstNode(name='traverseFunction',
                    type='MethodDeclaration', start_pos=334, end_pos=348),
        JavaAstNode(name='collectMaybeUnreferencedVars',
                    type='MethodDeclaration', start_pos=354, end_pos=361),
        JavaAstNode(name='removeUnreferencedFunctionArgs',
                    type='MethodDeclaration', start_pos=369, end_pos=409),
        JavaAstNode(name='getFunctionArgList',
                    type='MethodDeclaration', start_pos=415, end_pos=417),
        JavaAstNode(name='CallSiteOptimizer',
                    type='ClassDeclaration', start_pos=419, end_pos=702),
        JavaAstNode(name='CallSiteOptimizer',
                    type='ConstructorDeclaration', start_pos=425, end_pos=430),
        JavaAstNode(name='optimize', type='MethodDeclaration',
                    start_pos=432, end_pos=443),
        JavaAstNode(name='applyChanges', type='MethodDeclaration',
                    start_pos=448, end_pos=457),
        JavaAstNode(name='markUnreferencedFunctionArgs',
                    type='MethodDeclaration', start_pos=472, end_pos=510),
        JavaAstNode(name='canRemoveArgFromCallSites',
                    type='MethodDeclaration', start_pos=517, end_pos=535),
        JavaAstNode(name='tryRemoveArgFromCallSites',
                    type='MethodDeclaration', start_pos=541, end_pos=566),
        JavaAstNode(name='tryRemoveAllFollowingArgs',
                    type='MethodDeclaration', start_pos=571, end_pos=585),
        JavaAstNode(name='getArgumentForCallOrNewOrDotCall',
                    type='MethodDeclaration', start_pos=591, end_pos=599),
        JavaAstNode(name='canModifyCallers',
                    type='MethodDeclaration', start_pos=605, end_pos=624),
        JavaAstNode(name='isModifiableCallSite',
                    type='MethodDeclaration', start_pos=630, end_pos=633),
        JavaAstNode(name='canChangeSignature',
                    type='MethodDeclaration', start_pos=639, end_pos=687),
        JavaAstNode(name='getFunctionDefinition',
                    type='MethodDeclaration', start_pos=693, end_pos=701),
        JavaAstNode(name='interpretAssigns',
                    type='MethodDeclaration', start_pos=724, end_pos=773),
        JavaAstNode(name='removeAllAssigns',
                    type='MethodDeclaration', start_pos=778, end_pos=783),
        JavaAstNode(name='markReferencedVar',
                    type='MethodDeclaration', start_pos=790, end_pos=798),
        JavaAstNode(name='removeUnreferencedVars',
                    type='MethodDeclaration', start_pos=804, end_pos=870),
        JavaAstNode(name='Continuation', type='ClassDeclaration',
                    start_pos=877, end_pos=896),
        JavaAstNode(name='Continuation',
                    type='ConstructorDeclaration', start_pos=881, end_pos=884),
        JavaAstNode(name='apply', type='MethodDeclaration',
                    start_pos=886, end_pos=895),
        JavaAstNode(name='Assign', type='ClassDeclaration',
                    start_pos=898, end_pos=997),
        JavaAstNode(name='Assign', type='ConstructorDeclaration',
                    start_pos=922, end_pos=933),
        JavaAstNode(name='maybeCreateAssign',
                    type='MethodDeclaration', start_pos=939, end_pos=965),
        JavaAstNode(name='remove', type='MethodDeclaration',
                    start_pos=970, end_pos=996),
    ]
    result_nodes = load_ast_nodes(file_path)
    assert len(result_nodes) == 35
    for i in range(len(result_nodes)):
        assert result_nodes[i].__eq__(expect_nodes[i])


def test_load_fixed_code_node():
    countable_diffs = load_patch_file(
        "src/fixtures/Defects4J_Closure_01.patch")
    file_path = "src/fixtures/Defects4J_Closure_01_fixed.source"
    result = load_fixed_code_node(
        file_path, countable_diffs[0].sorted_changes())
    expect = JavaAstNode(name='removeUnreferencedFunctionArgs',
                         type='MethodDeclaration', start_pos=369, end_pos=409)
    expect.highlight_line_numbers = [379, 380]
    assert result.__eq__(expect)


def test_get_node_by_hash():
    fixed_file_path = "src/fixtures/Defects4J_Closure_01_fixed.source"
    buggy_file_path = "src/fixtures/Defects4J_Closure_01_buggy.source"
    patch_file_path = 'src/fixtures/Defects4J_Closure_01.patch'
    countable_diffs = load_patch_file(patch_file_path)
    fixed_node = load_fixed_code_node(
        fixed_file_path, countable_diffs[0].sorted_changes())
    buggy_nodes = load_ast_nodes(buggy_file_path)
    buggy_node = get_node_by_hash(buggy_nodes, fixed_node.hash)
    print('fixed_node: ', fixed_node)
    print('buggy_node: ', buggy_node)
    assert buggy_node.hash == fixed_node.hash
