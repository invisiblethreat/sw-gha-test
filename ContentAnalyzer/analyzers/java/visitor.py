"""Java Visitor"""

from typing import Tuple, Union

from javalang.ast import Node


class Visitor:
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

    def visit_SuperConstructorInvocation(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_ClassReference(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_TypeArgument(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_AnnotationDeclaration(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_InterfaceDeclaration(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_ContinueStatement(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_ConstantDeclaration(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_EnhancedForControl(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_TypeParameter(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_ExplicitConstructorInvocation(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_SuperMethodInvocation(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_AnnotationMethod(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_DoStatement(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_SynchronizedStatement(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_EnumDeclaration(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_EnumConstantDeclaration(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_EnumBody(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_InferredFormalParameter(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_LambdaExpression(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_TryResource(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_MethodReference(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_SuperMemberReference(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    def visit_AssertStatement(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        print("", end='')
        return node

    # pylint: enable=unused-argument,missing-docstring,line-too-long,no-self-use
