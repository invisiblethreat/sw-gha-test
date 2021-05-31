import sys
import antlr4
from antlr4.tree.Tree import TerminalNodeImpl
from ContentAnalyzer.analyzers.python import Python3Lexer
from ContentAnalyzer.analyzers.python import Python3Parser
from ContentAnalyzer.analyzers.python import AnalyzerPython3Visitor

def main():
    test_filename = "./antlr/python/samples/sample5.py"

    filename = test_filename

    i_stream = antlr4.FileStream(filename)
    print("=" * 80)
    print("python_antlr4.py")
    print(filename)
    print("=" * 80)

    lexer = Python3Lexer(i_stream)

    stream = antlr4.CommonTokenStream(lexer)
    parser = Python3Parser(stream)

    tree = parser.file_input()

    visitor = AnalyzerPython3Visitor()

    visitor.visit(tree)
    for kvp in visitor.get_matches():
        print("'%s' => '%s'" % (kvp.key, kvp.value))


if __name__ == "__main__":
    main()
