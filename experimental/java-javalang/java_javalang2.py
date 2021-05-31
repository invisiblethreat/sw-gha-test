"""Javalang"""

from typing import Tuple, Union

import javalang
from javalang.ast import Node


def read_contents(filename: str) -> str:
    """Read contents of file"""

    f = open(filename, 'r', encoding='utf-8')
    content = f.read()
    f.close()
    return content


class JavaVisitor:
    """Java Visitor"""

    def __init__(self):

        self.tree = None

    def visit(self, tree):
        self.tree = tree

        for child in tree.children:
            self.walk(child, tuple())

    def walk(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        if isinstance(node, Node):
            pass
        elif isinstance(node, (list, tuple)):
            for child in node:
                self.walk(child, ctx)
            return
        else:
            return

        kind = node.__class__.__name__
        method_name = f"visit_{kind}"
        method = getattr(self, method_name)

        new_node = method(node, ctx)

        if new_node is not None:
            for child in new_node.children:
                self.walk(child, new_node)


    # pylint: disable=unused-argument,missing-docstring,line-too-long,no-self-use
    def visit_FieldDeclaration(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_CompilationUnit(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_PackageDeclaration(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_ReferenceType(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_Import(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_ClassDeclaration(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_BasicType(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_VariableDeclarator(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_Literal(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_MethodInvocation(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_ArrayCreator(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_ArrayInitializer(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_MethodDeclaration(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_ReturnStatement(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_This(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_MemberReference(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_TernaryExpression(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_BinaryOperation(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_Cast(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_ClassCreator(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_FormalParameter(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_StatementExpression(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_Assignment(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_LocalVariableDeclaration(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_TryStatement(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_CatchClause(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_CatchClauseParameter(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_IfStatement(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_BlockStatement(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_WhileStatement(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_SwitchStatement(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_SwitchStatementCase(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_BreakStatement(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_ThrowStatement(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_ForStatement(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_ForControl(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_VariableDeclaration(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_ArraySelector(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_Annotation(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_ElementValuePair(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_ElementArrayValue(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_ConstructorDeclaration(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node
    # pylint: enable=unused-argument,missing-docstring,line-too-long,no-self-use


def main():
    """Main."""

    filename = "tests/data/java/sample3.java"
    content = read_contents(filename)

    tree = javalang.parse.parse(content)

    visitor = JavaVisitor()
    visitor.visit(tree)

    print("", end='')


if __name__ == "__main__":
    main()
