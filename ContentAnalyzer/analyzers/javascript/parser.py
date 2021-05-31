"""Javascript Parser/Visitor"""

from typing import List, Tuple, TypeVar

import esprima

from ContentAnalyzer import LineColumnLocation
from ContentAnalyzer.base import PosCalculate, KeyValuePair


def is_Identifier(node) -> bool:
    if node is None:
        return False
    return node.type == "Identifier"

def is_VariableDeclarator(node) -> bool:
    if node is None:
        return False
    return node.type == "VariableDeclarator"

def is_Property(node) -> bool:
    if node is None:
        return False
    return node.type == "Property"

def is_ExpressionStatement(node) -> bool:
    if node is None:
        return False
    return node.type == "ExpressionStatement"

def is_AssignmentExpression(node) -> bool:
    if node is None:
        return False
    return node.type == "AssignmentExpression"

def is_MemberExpression(node) -> bool:
    if node is None:
        return False
    return node.type == "MemberExpression"

def is_Literal(node) -> bool:
    if node is None:
        return False
    return node.type == "Literal"

def is_LiteralStr(node) -> bool:
    if is_Literal(node):
        return isinstance(node.value, str)
    return False


def is_LogicalExpression(node) -> bool:
    """Node is a LogicalExpression"""
    return isinstance(node, esprima.nodes.BinaryExpression) and node.type == "LogicalExpression"


def is_LeftOrRightLiteral(node) -> Tuple[bool, bool]:
    """Check if node left or right is a string literal."""
    left = False
    right = False
    if hasattr(node, 'left'):
        left = is_Literal(node.left)
    if hasattr(node, 'right'):
        right = is_Literal(node.right)
    return left, right


class Visitor(esprima.NodeVisitor):
    """Visitor"""

    def __init__(self, text: str = None):
        super().__init__()
        self.matches = []
        # self.line_positions: List[int] = line_positions
        self.pos_calculate = PosCalculate(text=text)

    def get_matches(self) -> List[KeyValuePair]:
        """Get list of KeyValuePairs.

        Returns:
            list: List of KeyValuePair.
        """
        return self.matches.copy()

    def make_node_key_value_pair(self, node: TypeVar('EsprimaNode')) -> KeyValuePair:
        """Make a node KeyValuePair.

        Args:
            node (TypeVar): EsprimaNode.

        Raises:
            TypeError: If left side node can not be determined.
            TypeError: If node type can not be determined.

        Returns:

            KeyValuePair: KeyValuePair for node.
        """
        if is_VariableDeclarator(node):
            key = node.id
            value = node.init
        elif is_Property(node):
            key = node.key
            value = node.value
        elif is_AssignmentExpression(node):
            value = node.right
            if is_MemberExpression(node.left):
                key = node.left.property
            elif is_Identifier(node.left):
                key = node.left
            else:
                raise TypeError("Could not determine left side node type!")
        else:
            raise TypeError("Could not determine node type!")
        return self.make_key_value_pair(key, value)


    # pylint: disable=line-too-long
    def make_key_value_pair(self, key_node: TypeVar('EsprimaNode'), value_node: TypeVar('EsprimaNode')) -> KeyValuePair:
        """Make a KeyValuePair from a pair of EsprimaNodes.

        Args:

            key_node (TypeVar): Key node or possible a string of the key?
            value_node (TypeVar): Value node.

        Returns:

            KeyValuePair: KeyValuePair for nodes.
        """

        key = LineColumnLocation(pos_calculate=self.pos_calculate)
        # key.from_esprima_node(key_node)
        key.from_node(key_node)
        value = LineColumnLocation(pos_calculate=self.pos_calculate)
        # value.from_esprima_node(value_node)
        value.from_node(value_node)
        kvp = KeyValuePair(key=key, value=value)
        self.matches.append(kvp)
        return kvp
    # pylint: disable=line-too-long


    def visit_BlockStatement(self, node: esprima.nodes.BlockStatement) -> None:
        # Make sure everything else gets visited:
        self.generic_visit(node)


    def visit_AssignmentExpression(self, node: esprima.nodes.AssignmentExpression) -> None:
        if is_LiteralStr(node.right):
            self.make_node_key_value_pair(node)
        else:
            # print("", end='')
            pass
        self.generic_visit(node)

    # def visit_ExpressionStatement(self, node):
    #     if is_AssignmentExpression(node.expression) and is_LiteralStr(node.expression.right):
    #         self.make_node_key_value_pair(node)
    #     else:
    #         print("", end='')
    #     self.generic_visit(node)


    def visit_VariableDeclarator(self, node: esprima.nodes.VariableDeclarator) -> None:
        if hasattr(node, 'init') and is_LiteralStr(node.init):
            self.make_node_key_value_pair(node)
        else:
            # print("", end='')
            pass
        self.generic_visit(node)


    def visit_Property(self, node: esprima.nodes.Property) -> None:
        """Property node.

        Used for objects typically I think.
        """

        if is_LiteralStr(node.value):
            self.make_node_key_value_pair(node)
            # Don't recurse (visit)
            return
        elif is_LogicalExpression(node.value):
            expression_node = node.value
            left, right = is_LeftOrRightLiteral(expression_node)
            if left:
                self.make_key_value_pair(node.key, expression_node.left)
            if right:
                self.make_key_value_pair(node.key, expression_node.right)
            if left or right:
                # Don't recurse (visit)
                return
        else:
            pass
        self.generic_visit(node)


    def visit_CallExpression(self, node: esprima.nodes.CallExpression) -> None:
        """CallExpression.

        Function with arguments basically.
        """
        # function = node.callee.name
        function_node = node.callee

        for argument in node.arguments:
            # Check each argument for string literals
            if isinstance(argument, esprima.nodes.Literal):
                # Check that the value of the literal is a string and not a bool or int
                if isinstance(argument.value, str):
                    if not isinstance(function_node, esprima.nodes.StaticMemberExpression):
                        # If function_node is a MemberExpression it requires a lot of
                        # tree traversal to resolve its name and from what I've observed
                        # thus far it is heavily used for jQuery type stuff which
                        # uses prepended '$' in function calls.
                        value_node = argument
                        self.make_key_value_pair(function_node, value_node)
            else:
                self.generic_visit(argument)
        self.generic_visit(node.callee)


    def visit_ObjectExpression(self, node: esprima.nodes.ObjectExpression) -> None:
        """ObjectExpression.

        Seen when doing module.exports = {}
        """

        object_node = node

        for property_node in object_node.properties:
            if isinstance(property_node, esprima.nodes.Property):
                self.visit_Property(property_node)

        # Don't visit (recurse) otherwise we could end up making a lot of duplicate kvps
        # self.generic_visit(node)
