import ast
from pprint import pprint

class Analyzer(ast.NodeVisitor):
    def __init__(self):
        self.stats = {"import": [], "from": []}

    def visit_Import(self, node):
        for alias in node.names:
            self.stats["import"].append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.stats["from"].append(alias.name)
        self.generic_visit(node)

    def report(self):
        pprint(self.stats)

def main():
    filename = "./antlr/python/samples/sample7.py"
    with open(filename, "r") as source:
        tree = ast.parse(source.read())

    print(ast.dump(tree))

    # analyzer = Analyzer()
    # analyzer.visit(tree)
    # analyzer.report()

if __name__ == "__main__":
    main()