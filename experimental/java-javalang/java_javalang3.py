"""Javalang"""

from typing import Tuple, Union

import javalang
from javalang.ast import Node

from ContentAnalyzer import KeyValuePair, LineColumnLocation
from ContentAnalyzer.base import PosCalculate

def read_contents(filename: str) -> str:
    """Read contents of file"""

    f = open(filename, 'r', encoding='utf-8')
    content = f.read()
    f.close()
    return content


class JavaVisitor:
    """Java Visitor.

    Attributes:

        tree (Node): Tree that was visited.
    """

    def __init__(self):

        self.tree = None

    def visit(self, tree: Node) -> None:
        """Visit a javalang Tree.

        Args:

            tree (Node): javalang tree to visit.

        Returns:

            None.
        """
        self.tree = tree

        for child in tree.children:
            self.walk(child, tuple())


    def walk(self, node: Node, ctx: Union[Node, Tuple]) -> None:
        """Walk a node and it's children.

        Walk a node and the children of whatever node is returned to the visiting method.

        Args:

            node (Node): Java parser node.
            ctx (Union[Node, Tuple]): Parent context or None.

        Returns:

            None.
        """
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


class MyVisitor(JavaVisitor):
    """MyVisitor"""


    def __init__(self, pos_calculate: PosCalculate = None):
        super().__init__()
        self.pos_calculate = pos_calculate
        self.contexts = []
        self.keys = []
        self.key = None
        self.value = None

        self.matches = []


    def set_state(self, node: Node) -> None:
        """Set and maintain state for key/value pairs.

        Args:

            node (Node): Node to add to state.

        Returns:

            None.
        """
        kind = node.__class__.__name__

        if kind == "VariableDeclarator":
            self.key = node

        elif kind == "MethodInvocation":
            # Need to visit child nodes so store our "state"
            # as the last MethodInovcation so that added
            # Literals match up properly.
            self.contexts.append(node)

            # Store current key (even if it is None) in
            # self.keys to preserve state when pop ourselves
            # from stack.
            self.keys.append(self.key)
            self.key = None

            for child in node.children:
                self.walk(child, node)

            self.key = self.keys.pop()
            self.contexts.pop()

        elif kind == "Literal":
            if self.contexts:
                # We're iterating on MethodInvocation currently
                # so this Literal belongs to it
                key_node = self.contexts[-1]
                name = key_node.member
            else:
                if self.key is None:
                    return

            key_kind = self.key.__class__.__name__
            if key_kind == "VariableDeclarator":
                name = self.key.name
                key_node = self.key

            self.value = node
            value_node = node
            value = self.value.value

            if value.startswith('"') and value.startswith('"'):
                # This is a string so parse it
                self.make_key_value_pair(key_node, value_node)
                print(name, end=' => ')
                print(self.value.value)
            self.key = None
            self.value = None


    # pylint: disable=line-too-long
    def make_key_value_pair(self, key_node: Node, value_node: Node) -> KeyValuePair:
        """Make a KeyValuePair from a pair of EsprimaNodes.

        Args:

            key_node (TypeVar): Key node or possible a string of the key?
            value_node (TypeVar): Value node.

        Returns:

            KeyValuePair: KeyValuePair for nodes.
        """

        key = LineColumnLocation(pos_calculate=self.pos_calculate)
        key.from_javalang_node(key_node)
        value = LineColumnLocation(pos_calculate=self.pos_calculate)
        value.from_javalang_node(value_node)
        kvp = KeyValuePair(key=key, value=value)
        self.matches.append(kvp)
        return kvp
    # pylint: disable=line-too-long


    def visit_VariableDeclarator(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        # print(node.name)
        # if not hasattr(node, 'position'):
        if node.position is None:
            # This happens in cases like this:
            # String[] pvtkwds = new String[]{"", "exp"};
            # Best I can do for now
            node._position = ctx.position # pylint: disable=protected-access
        self.set_state(node)
        print("", end='')
        return node


    def visit_MethodInvocation(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        self.set_state(node)
        print("", end='')
        # Don't return node as set_state will iterate over our children
        # return node


    def visit_Literal(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        # print(node.value)
        self.set_state(node)



def main():
    """Main."""

    filename = "tests/data/java/sample4.java"
    content = read_contents(filename)

    tree = javalang.parse.parse(content)

    # visitor = JavaVisitor()
    pos_calculate = PosCalculate(text=content)
    visitor = MyVisitor(pos_calculate=pos_calculate)
    visitor.visit(tree)

    print("", end='')


if __name__ == "__main__":
    main()
