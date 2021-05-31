"""Javascript Parser/Visitor"""

from __future__ import annotations

from typing import List, Tuple, TypeVar

import esprima


class Identifier:
    """Identifier"""

    def __call__(self):
        return self.value

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<{self.__class__.__name__} name=\"{self.name}\">"

    def __init__(self, node):
        self.name = node.name
        # self.value = None

    def assign(self, value):
        self.value = value


    def children(self) -> List:
        """Return children"""
        return list()

class Literal:
    """Literal"""

    def __str__(self):
        value = self.value
        if isinstance(value, (int, float)):
            rval = str(value)
        elif isinstance(value, str):
            rval = f'"{value}"'
        elif isinstance(value, bool):
            rval = "True" if value else "False"
        elif value is None:
            rval = ""
        return rval

    def __repr__(self):
        return f"<{self.__class__.__name__} value={str(self)}>"

    def eval(self):
        return self.value

    def __init__(self, node):
        self.value = node.value
        self.stop = False
        self.left_stop = False
        self.right_stop = False

    def is_str(self) -> bool:
        """Literal is string?"""
        return isinstance(self.value, str)

    def is_int(self) -> bool:
        """Literal is int?"""
        return isinstance(self.value, int)

    def is_float(self) -> bool:
        """Literal is float?"""
        return isinstance(self.value, float)

    def is_number(self) -> bool:
        """Literal is number?"""
        return isinstance(self.value, (int, float))

    def is_bool(self) -> bool:
        """Literal is bool?"""
        return isinstance(self.value, bool)

    def is_null(self) -> bool:
        """Literal is null?"""
        return self.value is None

    def is_none(self) -> bool:
        """Literal is None?"""
        return self.value is None

    def children(self) -> List:
        """Return children"""
        return list()

class BinaryExpression:
    """BinaryExpression"""

    def __str__(self):
        return f"({str(self.left)} {self.operator} {str(self.right)})"

    def __repr__(self):
        return f"<{self.__class__.__name__} value={str(self)}>"

    def eval(self):
        op = self.operator
        l_value = self.left()
        r_value = self.right()

        if op == "||":
            result = l_value or r_value
        elif op == "&&":
            result = l_value and r_value
        elif op == "!=":
            result = l_value != r_value
        elif op == "==":
            result = l_value == r_value
        elif op == ">":
            result = l_value > r_value
        elif op == "<":
            result = l_value < r_value
        elif op == ">=":
            result = l_value >= r_value
        elif op == "<=":
            result = l_value <= r_value
        else:
            raise TypeError(f"Don't know how to handle op '{op}'")

        self.result = result
        return result

    def __init__(self, node):
        self.left = get_node_class(node.left, self)
        self.right = get_node_class(node.right, self)
        self.operator = node.operator
        self.result = None


    def children(self) -> List:
        """Return children"""
        return [self.left, self.right]

class UpdateExpression:
    """UpdateExpression"""

    def __str__(self):
        return f"{self.__class__.__name__} {self.prefix} {self.operator}"

    def __repr__(self):
        return f"<{self.__class__.__name__} value={str(self)}>"

    def __init__(self, node):
        self.argument = get_node_class(node.argument, self)
        self.prefix = node.prefix
        self.operator = node.operator


    def children(self) -> List:
        """Return children"""
        return [self.argument]

# class LogicalExpression(BinaryExpression):
#     """LogicalExpression"""

class ConditionalExpression:
    """ConditionalExpression"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __call__(self):
        test = self.test
        consequent = self.consequent
        alternate = self.alternate
        if test:
            result = consequent()
        result = alternate()
        self.result = result
        return result

    def __init__(self, node):
        self.test = get_node_class(node.test, self)
        self.consequent = get_node_class(node.consequent, self)
        self.alternate = get_node_class(node.alternate, self)
        self.result = None

    def children(self) -> List:
        """Return children"""
        children = list()
        props = ('test', 'consequent', 'alternate')
        for prop in props:
            value = getattr(self, prop)
            if value is not None:
                children.append(value)
        return children

class VariableDeclarator:
    """VariableDeclarator"""

    def __str__(self):
        # value = self.value or ""
        return f"{str(self.id)} = {str(self.init)}"

    def __repr__(self):
        return f"<{self.__class__.__name__} {str(self)}>"

    def __call__(self):
        self.value = self.init()
        return self.value

    def display(self):
        value = self.value or ""
        return f"{str(self.id)} = {str(value)}"

    def __init__(self, node):
        self.id = get_node_class(node.id, self)
        self.init = get_node_class(node.init, self)
        self.value = None
        self.name = self.id

    def children(self) -> List:
        """Return children"""
        children = list()
        props = ('id', 'init')
        for prop in props:
            value = getattr(self, prop)
            if value is not None:
                children.append(value)

        return children

class VariableDeclaration:
    """VariableDeclaration"""

    def __str__(self):
        if not self.declarations:
            declarations = ""
        else:
            declarations = ", ".join([str(n) for n in self.declarations])
        return f"{self.kind} {declarations}"

    def __repr__(self):
        return f"<{self.__class__.__name__} kind={str(self)}>"

    def __call__(self):
        for declarations in self.declarations:
            declarations()

    def __init__(self, node):
        self.declarations = [get_node_class(n, self) for n in node.declarations]
        self.value = None
        self.kind = node.kind

    def children(self) -> List:
        """Return children"""
        return [self.declarations]

class FunctionDeclaration:
    """FunctionDeclaration"""

    def __str__(self):
        # name = "<ANONYMOUS>"
        # if self.id is not None and hasattr(self.id, 'name'):
        #     name = self.id.name
        # return name
        if not self.params:
            params = ""
        else:
            params = ", ".join([str(n) for n in self.params])
        return f"function {str(self.id)}({params}) {{\n{str(self.body)}\n}}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):
        self.params = [get_node_class(n, self) for n in node.params]
        self.body = get_node_class(node.body, self)
        self.expression = node.expression
        self.generator = node.generator
        self.id = get_node_class(node.id, self)
        self.is_async = node.isAsync

        if self.id is not None and hasattr(self.id, 'name'):
            self.name = self.id.name

    def children(self) -> List:
        """Return children"""
        children = list()
        props = ('params', 'body', 'id')
        for prop in props:
            value = getattr(self, prop)
            if value is not None:
                children.append(value)
        return children

class ArrowFunctionExpression:
    """ArrowFunctionExpression"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):
        self.params = [get_node_class(n, self) for n in node.params]
        self.body = get_node_class(node.body, self)
        self.expression = node.expression
        self.generator = node.generator
        self.is_async = node.isAsync

    def children(self) -> List:
        """Return children"""
        children = list()
        props = ('params', 'body')
        for prop in props:
            value = getattr(self, prop)
            if value is not None:
                children.append(value)
        return children

class BlockStatement:
    """BlockStatement"""

    def __str__(self):
        block = "\n".join([str(statement) for statement in self.statements])
        return f"{block}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __call__(self):
        for statement in self.statements:
            statement()

    def __init__(self, node):
        self.statements = [get_node_class(n, self) for n in node.body]

    def children(self) -> List:
        """Return children"""
        return [self.statements]

class TryStatement:
    """TryStatement"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__} >"

    def __init__(self, node):
        self.block = get_node_class(node.block, self)
        self.finalizer = get_node_class(node.finalizer, self)
        self.handler = get_node_class(node.handler, self)

    def children(self) -> List:
        """Return children"""
        children = list()
        props = ('block', 'finalizer', 'handler')
        for prop in props:
            value = getattr(self, prop)
            if value is not None:
                children.append(value)
        return children

class EmptyStatement:
    """EmptyStatement"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):
        pass

    def children(self) -> List:
        """Return children"""
        return list()

class ThrowStatement:
    """ThrowStatement"""

    def __str__(self):
        return f"throw({str(self.argument)})"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):
        self.argument = get_node_class(node.argument, self)

    def children(self) -> List:
        """Return children"""
        return [self.argument]

class BreakStatement:
    """BreakStatement"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):
        self.label = None
        if isinstance(node.label, str):
            self.label = node.label
        elif node.label is not None:
            self.label = get_node_class(node.label, self)

    def children(self) -> List:
        """Return children"""
        if self.label is None:
            return list()
        return [self.label]

class CatchClause:
    """CatchClause"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):
        self.body = get_node_class(node.body, self)
        self.param = get_node_class(node.param, self)

    def children(self) -> List:
        """Return children"""
        children = list()
        props = ('body', 'param')
        for prop in props:
            value = getattr(self, prop)
            if value is not None:
                children.append(value)
        return children

class WhileStatement:
    """WhileStatement"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):
        self.body = get_node_class(node.body, self)
        self.test = get_node_class(node.test, self)

    def children(self) -> List:
        """Return children"""
        children = list()
        props = ('body', 'test')
        for prop in props:
            value = getattr(self, prop)
            if value is not None:
                children.append(value)
        return children

class UnaryExpression:
    """UnaryExpression"""

    def __str__(self):
        return f"{self.operator} {str(self.argument)}"

    def __repr__(self):
        return f"<{self.__class__.__name__} value={str(self)}>"

    def __call__(self):
        return None

    def __init__(self, node):
        self.argument = get_node_class(node.argument, self)
        self.operator: str = node.operator
        self.prefix: bool = node.prefix


    def children(self) -> List:
        """Return children"""
        return [self.argument]

class AssignmentExpression:
    """AssignmentExpression"""

    def __str__(self):
        return self.operator

    def __repr__(self):
        return f"<{self.__class__.__name__} value={str(self)}>"

    def __call__(self):
        self.result = self.right()
        self.left.assign(self.result)

    def __init__(self, node):
        self.left = get_node_class(node.left, self)
        self.right = get_node_class(node.right, self)
        self.operator = node.operator
        self.result = None

    def children(self) -> List:
        """Return children"""
        children = list()
        props = ('left', 'right')
        for prop in props:
            value = getattr(self, prop)
            if value is not None:
                children.append(value)
        return children

class ExpressionStatement:
    """ExpressionStatement"""

    def __str__(self):
        return f"{str(self.expression)}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __call__(self):
        return self.expression()

    def __init__(self, node):
        self.expression = get_node_class(node.expression, self)

    def children(self) -> List:
        """Return children"""
        return [self.expression]

class SequenceExpression:
    """SequenceExpression"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __call__(self):
        for expression in self.expressions:
            expression()

    def __init__(self, node):
        self.expressions = [get_node_class(n, self) for n in node.expressions]

    def children(self) -> List:
        """Return children"""
        return [self.expressions]

class ObjectExpression:
    """ObjectExpression"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __call__(self):
        for prop in self.properties:
            prop()

    def __init__(self, node):
        self.properties = [get_node_class(n, self) for n in node.properties]

    def children(self) -> List:
        """Return children"""
        return [self.properties]

class StaticMemberExpression:
    """StaticMemberExpression"""

    def __str__(self):
        rval = f"{str(self.object)}({str(self.property)})"
        return rval

    def __repr__(self):
        return f"<{self.__class__.__name__} value={str(self)}>"

    def __init__(self, node):
        self.object = get_node_class(node.object, self)
        self.property = get_node_class(node.property, self)

    def assign(self, value):
        self.property.assign(value)

    def children(self) -> List:
        """Return children"""
        children = list()
        props = ('object', 'property')
        for prop in props:
            value = getattr(self, prop)
            if value is not None:
                children.append(value)
        return children

class ComputedMemberExpression:
    """ComputedMemberExpression"""

    def __str__(self):
        rval = f"{str(self.object)}({str(self.property)})"
        return rval

    def __repr__(self):
        return f"<{self.__class__.__name__} value={str(self)}>"

    def __init__(self, node):
        self.object = get_node_class(node.object, self)
        self.property = get_node_class(node.property, self)

    def assign(self, value):
        self.property.assign(value)

    def children(self) -> List:
        """Return children"""
        children = list()
        props = ('object', 'property')
        for prop in props:
            value = getattr(self, prop)
            if value is not None:
                children.append(value)
        return children

class CallExpression:
    """CallExpression"""

    def __str__(self):
        if not self.arguments:
            arguments = ""
        else:
            arguments = ", ".join([str(n) for n in self.arguments])
        return f"{str(self.callee)}({arguments})"

    def __repr__(self):
        return f"<{self.__class__.__name__} value={str(self)}>"

    def __init__(self, node):
        self.callee = get_node_class(node.callee, self)
        self.arguments = [get_node_class(n, self) for n in node.arguments]
        print("", end='')

    def children(self) -> List:
        """Return children"""
        children = list()
        props = ('callee', 'arguments')
        for prop in props:
            value = getattr(self, prop)
            if value is not None:
                children.append(value)
        return children

class FunctionExpression:
    """FunctionExpression"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):
        # self.callee = get_node_class(node.callee, self)
        # self.arguments = [get_node_class(n, self) for n in node.arguments]
        self.body = get_node_class(node.body, self)
        self.params = [get_node_class(n, self) for n in node.params]
        print("", end='')

    def children(self) -> List:
        """Return children"""
        children = list()
        props = ('body', 'params')
        for prop in props:
            value = getattr(self, prop)
            if value is not None:
                children.append(value)
        return children

class ArrayExpression:
    """ArrayExpression"""

    def __str__(self):
        if not self.elements:
            elements = ""
        else:
            elements = ", ".join([str(n) for n in self.elements])
        return f"[{elements}];"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):
        self.elements = [get_node_class(n, self) for n in node.elements]
        print("", end='')

    def children(self) -> List:
        """Return children"""
        return [self.elements]

class ReturnStatement:
    """ReturnStatement"""

    def __str__(self):
        return f"return {str(self.argument)}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):
        self.argument = get_node_class(node.argument, self)
        print("", end='')

    def children(self) -> List:
        """Return children"""
        if self.argument is not None:
            return [self.argument]
        return list()

class NewExpression:
    """NewExpression"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):
        self.callee = get_node_class(node.callee, self)
        self.arguments = [get_node_class(n, self) for n in node.arguments]
        print("", end='')

    def children(self) -> List:
        """Return children"""
        children = list()
        props = ('callee', 'arguments')
        for prop in props:
            value = getattr(self, prop)
            if value is not None:
                children.append(value)
        return children

class RegexLiteral:
    """RegexLiteral"""

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"<{self.__class__.__name__} value={str(self)}>"

    def __init__(self, node):
        self.raw = node.raw
        self.value = node.value
        self.regex = node.regex
        print("", end='')

    def children(self) -> List:
        """Return children"""
        return list()

class Property:
    """Property"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):
        self.key = get_node_class(node.key, self)
        self.value = get_node_class(node.value, self)
        if isinstance(self.key, Property):
            self.name = self.key.value
        elif isinstance(self.key, Literal):
            self.name = self.key.value
        else:
            self.name = self.key.name
        print("", end='')

    def children(self) -> List:
        """Return children"""
        children = list()
        props = ('key', 'value')
        for prop in props:
            value = getattr(self, prop)
            if value is not None:
                children.append(value)
        return children

class IfStatement:
    """IfStatement"""

    def __str__(self):
        rval = f"if ({str(self.test)}) {{\n{str(self.consequent)}\n}}"
        if self.alternate is not None:
            rval += f" else {{\n{str(self.alternate)})\n}}"
        return rval

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __call__(self):
        test = self.test
        consequent = self.consequent
        alternate = self.alternate
        if test:
            result = consequent()
        else:
            if alternate is None:
                result = None
            else:
                resul = alternate
        self.result = result
        return result

    def __init__(self, node):
        self.test = get_node_class(node.test, self)
        self.consequent = get_node_class(node.consequent, self)
        self.alternate = get_node_class(node.alternate, self)
        self.result = None

    def children(self) -> List:
        """Return children"""
        children = list()
        props = ('test', 'consequent', 'alternate')
        for prop in props:
            value = getattr(self, prop)
            if value is not None:
                children.append(value)
        return children

class DoWhileStatement:
    """DoWhileStatement"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):
        self.body = get_node_class(node.body, self)
        self.test = get_node_class(node.test, self)

    def children(self) -> List:
        """Return children"""
        children = list()
        props = ('body', 'test')
        for prop in props:
            value = getattr(self, prop)
            if value is not None:
                children.append(value)
        return children

class ThisExpression:
    """ThisExpression"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):
        if len(dir(node)) > 2:
            raise RuntimeError(f"node dir has more than 2 entries! {dir(node)}")

    def children(self) -> List:
        """Return children"""
        return list()

class ForInStatement:
    """ForInStatement"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):
        self.body = get_node_class(node.body, self)
        self.left = get_node_class(node.left, self)
        self.right = get_node_class(node.right, self)
        self.each = node.each

    def children(self) -> List:
        """Return children"""
        children = list()
        props = ('body', 'left', 'right')
        for prop in props:
            value = getattr(self, prop)
            if value is not None:
                children.append(value)
        return children

class ForStatement:
    """ForStatement"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):
        self.body = get_node_class(node.body, self)
        self.init = get_node_class(node.init, self)
        self.test = get_node_class(node.test, self)
        self.update = node.update

    def children(self) -> List:
        """Return children"""
        children = list()
        props = ('body', 'init', 'test')
        for prop in props:
            value = getattr(self, prop)
            if value is not None:
                children.append(value)
        return children

class ContinueStatement:
    """ContinueStatement"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):
        self.label = get_node_class(node.label, self)

    def children(self) -> List:
        """Return children"""
        return [self.label]

class SwitchStatement:
    """SwitchStatement"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):
        self.discriminant = get_node_class(node.discriminant, self)
        self.cases = [get_node_class(n, self) for n in node.cases]
        print("", end='')

    def children(self) -> List:
        """Return children"""
        children = list()
        props = ('discriminant', 'cases')
        for prop in props:
            value = getattr(self, prop)
            if value is not None:
                children.append(value)
        return children

class SwitchCase:
    """SwitchCase"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):
        self.test = get_node_class(node.test, self)
        self.consequent = [get_node_class(n, self) for n in node.consequent]
        print("", end='')

    def children(self) -> List:
        """Return children"""
        children = list()
        props = ('test', 'consequent')
        for prop in props:
            value = getattr(self, prop)
            if value is not None:
                children.append(value)
        return children

class LabeledStatement:
    """LabeledStatement"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):
        self.body = get_node_class(node.body, self)
        self.label = get_node_class(node.label, self)
        print("", end='')

    def children(self) -> List:
        """Return children"""
        children = list()
        props = ('body', 'label')
        for prop in props:
            value = getattr(self, prop)
            if value is not None:
                children.append(value)
        return children

class Directive:
    """Directive"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):
        self.directive = node.directive
        self.expression = get_node_class(node.expression, self)

    def children(self) -> List:
        """Return children"""
        return [self.expression]

class ObjectPattern:
    """ObjectPattern"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):
        self.properties = [get_node_class(n, self) for n in node.properties]

    def children(self) -> List:
        """Return children"""
        return [self.properties]

class TemplateLiteral:
    """TemplateLiteral"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):
        self.expressions = [get_node_class(n, self) for n in node.expressions]
        self.quasis = [get_node_class(n, self) for n in node.quasis]

    def children(self) -> List:
        """Return children"""
        children = list()
        props = ('expressions', 'quasis')
        for prop in props:
            value = getattr(self, prop)
            if value is not None:
                children.append(value)
        return children

class TemplateElement:
    """TemplateElement"""

    def __str__(self):
        return f"{self.__class__.__name__} => {self.tail} => {self.value}"

    def __repr__(self):
        return f"<{self.__class__.__name__} => {self.tail} => {self.value}>"

    def __init__(self, node):
        self.tail = node.tail
        self.value = node.value
        self.name = self.value.cooked

    def children(self) -> List:
        """Return children"""
        # return [self.value.cooked, self.value.raw]
        return list()

class ImportDeclaration:
    """ImportDeclaration"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):
        # self.source = get_node_class(node.source, self)
        self.specifiers = [get_node_class(n, self) for n in node.specifiers]

    def children(self) -> List:
        """Return children"""
        # children = list()
        # props = ('source', 'specifiers')
        # for prop in props:
        #     value = getattr(self, prop)
        #     if value is not None:
        #         children.append(value)
        # return children
        return [self.specifiers]

class ImportDefaultSpecifier:
    """ImportDefaultSpecifier"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):
        self.local = get_node_class(node.local, self)

    def children(self) -> List:
        """Return children"""
        # return [self.value.cooked, self.value.raw]
        return [self.local]

class ExportNamedDeclaration:
    """ExportNamedDeclaration"""

    def __str__(self):
        return f"{self.__class__.__name__}"

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __init__(self, node):

        self.declaration = get_node_class(node.declaration, self)
        self.specifiers = [get_node_class(n, self) for n in node.specifiers]

    def children(self) -> List:
        """Return children"""
        children = list()
        props = ('declaration', 'specifiers')
        for prop in props:
            value = getattr(self, prop)
            if value is not None:
                children.append(value)
        return children


ID_COUNTER = 1
GRAPH = list()
def get_node_class(obj, parent):
    """Get node class"""

    global ID_COUNTER
    global GRAPH

    if obj is None:
        return

    name = obj.__class__.__name__
    obj_class = globals().get(name, None)
    if obj_class is None:
        raise TypeError(f"Don't know how to get class for obj:\n{type(obj)}\n{dir(obj)}\n{[type(getattr(obj, n)) for n in dir(obj)]}")

    node = obj_class(obj)
    node.parent = parent
    node.node_id = ID_COUNTER

    GRAPH.append((parent, node))

    ID_COUNTER += 1
    return node


class Visitor(esprima.NodeVisitor):
    """Visitor"""

    def __init__(self, text: str = None):
        super().__init__()
        self.matches = []
        # self.line_positions: List[int] = line_positions
        # self.pos_calculate = PosCalculate(text=text)
        self.nodes = list()

    def get_matches(self) -> List['KeyValuePair']:
        """Get list of KeyValuePairs.

        Returns:
            list: List of KeyValuePair.
        """
        return self.matches.copy()

    def visit(self, obj) -> List:
        global ID_COUNTER
        for item in obj.body:
            node = get_node_class(item, None)
            self.nodes.append(node)
        ID_COUNTER = 1
        return self.nodes
