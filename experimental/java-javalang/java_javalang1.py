"""Javalang"""

import javalang
from javalang.ast import Node
import attr
from typing import Dict, List, Tuple, Union


def read_contents(filename: str) -> str:
    """Read contents of file"""

    f = open(filename, 'r', encoding='utf-8')
    content = f.read()
    f.close()
    return content


@attr.s(kw_only=True)
class JavaClassDeclaration():
    """JavaClassDeclaration."""

    node = attr.ib(default=None)
    children_methods = attr.ib(factory=list)
    children_fields = attr.ib(factory=list)

    @property
    def methods(self):
        """Get methods"""

        self.children_methods = []
        for m in self.node.methods:
            child_node = JavaMethodDeclaration(node=m)
            self.children_methods.append(child_node)

        return self.children_methods

    @property
    def string_arguments(self):
        """Get string_arguments"""
        args = []
        for child in self.methods:
            args.extend(child.string_arguments)

        return args

    @property
    def fields(self):
        """Get fields"""

        self.children_fields = []
        for m in self.node.fields:
            child_node = JavaField(node=m)
            self.children_fields.append(child_node)

        return self.children_fields

    @property
    def variable_assignments(self):
        """Get string_arguments"""
        args = []
        for child in self.fields:
            args.extend(child.declarators)

        return args


@attr.s(kw_only=True)
class JavaMethodDeclaration():
    """JavaMethodDeclaration."""

    node = attr.ib(default=None)
    children = attr.ib(default=None)

    @property
    def body(self):
        """Get body"""

        self.children = []
        for arg in self.node.body:
            if isinstance(arg, javalang.tree.StatementExpression):
                arg_node = JavaStatementExpression(node=arg)
                self.children.append(arg_node)
        return self.children

    @property
    def string_arguments(self):
        """Get string_arguments"""
        args = []
        for child in self.body:
            args.extend(child.string_arguments)

        return args


@attr.s(kw_only=True)
class JavaField():
    """JavaField."""

    node = attr.ib(default=None)
    children = attr.ib(default=None)

    @property
    def declarators(self):
        """Get declarators"""

        self.children = []
        if 'declarators' in self.node.attrs and self.node.declarators:
            for node in self.node.declarators:
                child_node = JavaVariableDeclarator(node=node)
                self.children.append(child_node)

        return self.children

    # @property
    # def string_arguments(self):
    #     """Get string_arguments"""
    #     args = []
    #     for child in self.declarators:
    #         args.extend(child.string_arguments)

    #     return args


@attr.s(kw_only=True)
class JavaVariableDeclarator():
    """JavaVariableDeclarator."""

    node = attr.ib(default=None)
    name: str = attr.ib(default=None)
    key: str = attr.ib(default=None)
    value: str = attr.ib(default=None)
    children = attr.ib(factory=list)


    def __attrs_post_init__(self):

        self.name = self.node.name
        self.key = self.node.name
        self.value = " ".join([n.value for n in self.string_arguments])


    @property
    def string_arguments(self):
        """Get declarator"""

        self.children = []
        for child in self.node.children:
            if isinstance(child, javalang.tree.Literal):
                child_node = JavaLiteral(node=child, parent_node=self)
                self.children.append(child_node)
            elif isinstance(child, javalang.tree.MethodInvocation):
                child_node = JavaMethodInvocation(node=child)
                self.children.extend(child_node.string_arguments)
            elif isinstance(child, javalang.tree.This):
                child_node = JavaThis(node=child)
                self.children.extend(child_node.string_arguments)
            elif isinstance(child, javalang.tree.Cast):
                child_node = JavaCast(node=child)
                self.children.extend(child_node.string_arguments)
        return self.children


@attr.s(kw_only=True)
class JavaStatementExpression():
    """JavaStatementExpression."""

    node = attr.ib(default=None)
    children = attr.ib(default=None)

    @property
    def expression(self):
        """Get expression"""

        return JavaMethodInvocation(node=self.node.expression)

    @property
    def string_arguments(self):
        """Get string_arguments"""
        return self.expression.string_arguments

@attr.s(kw_only=True)
class JavaMethodInvocation():
    """JavaMethodInvocation."""

    node = attr.ib(default=None)
    children = attr.ib(default=None)

    @property
    def name(self):
        """Get name"""

        return self.node.qualifier

    @property
    def value(self):
        return self.node.member


    @property
    def string_arguments(self):
        self.children = []
        if not hasattr(self.node, 'selectors') or not self.node.selectors:
            selectors = list()
        else:
            selectors = self.node.selectors
        for arg in selectors:
            if isinstance(arg, javalang.tree.Literal):
                arg_node = JavaLiteral(node=arg, parent_node=self)
                self.children.append(arg_node)
            elif isinstance(arg, javalang.tree.MethodInvocation):
                arg_node = JavaMethodInvocation(node=arg)
                self.children.extend(arg_node.string_arguments)
            elif isinstance(arg, javalang.tree.This):
                arg_node = JavaThis(node=arg)
                self.children.extend(arg_node.string_arguments)
            elif isinstance(arg, javalang.tree.Cast):
                arg_node = JavaCast(node=arg)
                self.children.extend(arg_node.string_arguments)
        if not hasattr(self.node, 'arguments') or not self.node.arguments:
            arguments = list()
        else:
            arguments = self.node.arguments
        for arg in arguments:
            if isinstance(arg, javalang.tree.Literal):
                arg_node = JavaLiteral(node=arg, parent_node=self)
                self.children.append(arg_node)
            elif isinstance(arg, javalang.tree.MethodInvocation):
                arg_node = JavaMethodInvocation(node=arg)
                self.children.extend(arg_node.string_arguments)
            elif isinstance(arg, javalang.tree.This):
                arg_node = JavaThis(node=arg)
                self.children.extend(arg_node.string_arguments)
            elif isinstance(arg, javalang.tree.Cast):
                arg_node = JavaCast(node=arg)
                self.children.extend(arg_node.string_arguments)
        return self.children

@attr.s(kw_only=True)
class JavaLiteral():
    """JavaLiteral."""

    node = attr.ib(default=None)
    parent_node = attr.ib(default=None)

    @property
    def key(self):
        """Get key"""
        if hasattr(self.parent_node, 'value'):
            return self.parent_node.value
        else:
            args = []
            for arg in self.parent_node.string_arguments:
                string_args = arg.string_arguments
                if not isinstance(string_args, list):
                    args.append(string_args)
                else:
                    args.extend(string_args)
            value = None
            for arg in args:
                if value is None:
                    value = ""
                value += arg.value
            return value
        # return self.parent_node.value

    @property
    def value(self):
        """Get value"""

        return self.node.value

    @property
    def string_arguments(self):
        """Get string_arguments"""

        return self


@attr.s(kw_only=True, slots=True)
class JavaThis():
    """JavaThis."""

    node = attr.ib(default=None)
    children = attr.ib(factory=list)

    @property
    def selectors(self):
        """Get selectors"""

        self.children = []
        selectors = self.node.selectors or list()
        for arg in selectors:
            if isinstance(arg, javalang.tree.Literal):
                arg_node = JavaLiteral(node=arg, parent_node=self)
                self.children.append(arg_node)
            elif isinstance(arg, javalang.tree.MethodInvocation):
                arg_node = JavaMethodInvocation(node=arg)
                self.children.extend(arg_node.string_arguments)
            elif isinstance(arg, javalang.tree.This):
                arg_node = JavaThis(node=arg)
                self.children.extend(arg_node.string_arguments)
            elif isinstance(arg, javalang.tree.Cast):
                arg_node = JavaCast(node=arg)
                self.children.extend(arg_node.string_arguments)
        return self.children

    @property
    def string_arguments(self):
        """Get string_arguments"""
        args = []
        for child in self.selectors:
            if not isinstance(child, str):
                args.append(child.string_arguments)
            else:
                args.append(child)

        return args

class JavaVisitor:
    """Java Visitor"""

    tree = attr.ib(default=None)

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
        # print("", end='')
        print(node.value)
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


class JavaTree:
    """JavaTree"""

    tree = attr.ib(default=None)
    visitor = attr.ib(default=None)

    def accept(self, visitor):
        self.visitor = visitor



@attr.s(kw_only=True)
class JavaCast():
    """JavaCast."""

    node = attr.ib(default=None)
    children = attr.ib(default=None)

    @property
    def expression(self):
        """Get expression"""
        arg = self.node.expression
        if isinstance(arg, javalang.tree.Literal):
            arg_node = JavaLiteral(node=arg, parent_node=self)
        elif isinstance(arg, javalang.tree.MethodInvocation):
            arg_node = JavaMethodInvocation(node=arg)
        elif isinstance(arg, javalang.tree.ArrayCreator):
            arg_node = JavaArrayCreator(node=arg)
        elif isinstance(arg, javalang.tree.MemberReference):
            arg_node = JavaMemberReference(node=arg)
        elif isinstance(arg, javalang.tree.This):
            arg_node = JavaThis(node=arg)
        return arg_node

    @property
    def string_arguments(self):
        """Get string_arguments"""
        blah = []
        shit = self.expression.string_arguments
        if not isinstance(shit, list):
            blah.append(shit)
        else:
            blah.extend(shit)
        # blah.extend(self.expression.string_arguments)
        return blah

@attr.s(kw_only=True, slots=True)
class JavaArrayCreator():
    """JavaArrayCreator."""

    node = attr.ib(default=None)

    @property
    def string_arguments(self):
        """Get string_arguments"""

        return list()

@attr.s(kw_only=True, slots=True)
class JavaMemberReference():
    """JavaMemberReference."""

    node = attr.ib(default=None)

    @property
    def string_arguments(self):
        """Get string_arguments"""

        return list()


def main():
    """Main."""


    filename = "tests/data/java/sample3.java"
    content = read_contents(filename)

    # tree = javalang.parse.parse("package javalang.brewtab.com; class Test {}")
    tree = javalang.parse.parse(content)

    jc = JavaClassDeclaration(node=tree.types[0]) # pylint: disable=no-member
    # print("================ String Arguments ================")
    # args = jc.string_arguments
    # for arg in args:
    #     print(arg.key, arg.value)
    #     print("-" * 80)
    # print("")
    # print("============== Variable Assignments ==============")
    # kvps = jc.variable_assignments
    # for kvp in kvps:
    #     print(kvp.key, kvp.value)
    #     print("-" * 80)

    # for path, node in tree:
    #     print(type(path), type(node))
    visitor = JavaVisitor()
    visitor.visit(tree)

    print("", end='')

if __name__ == "__main__":
    main()
