"""Java Visitor"""

from typing import List, Tuple, Union

from javalang.ast import Node

from ContentAnalyzer import LineColumnLocation
from ContentAnalyzer.analyzers.java.visitor import Visitor
from ContentAnalyzer.base import KeyValuePair, PosCalculate


class JavaVisitor(Visitor):
    """JavaVisitor"""


    def __init__(self, text: str = None):
        super().__init__()
        self.pos_calculate = PosCalculate(text=text)
        self.contexts = []
        self.keys = []
        self.key = None
        self.value = None

        self.matches = []


    def get_matches(self) -> List[KeyValuePair]:
        """Get list of KeyValuePairs.

        Returns:

            list: List of KeyValuePair.
        """
        return self.matches.copy()


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
                # name = key_node.member
            else:
                if self.key is None:
                    return

            key_kind = self.key.__class__.__name__
            if key_kind == "VariableDeclarator":
                # name = self.key.name
                key_node = self.key

            self.value = node
            value_node = node
            value = self.value.value

            if value.startswith('"') and value.startswith('"'):
                # This is a string so parse it
                self.make_key_value_pair(key_node, value_node)
                # print(name, end=' => ')
                # print(self.value.value)
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
        try:
            # key.from_javalang_node(key_node)
            key.from_node(key_node)
        except RuntimeError:
            # TODO: Work around for key nodes that have a missing position
            if hasattr(key_node, 'position'):
                if key_node.position is None:
                    key_node._position = value_node.position
                else:
                    raise
            else:
                raise
        value = LineColumnLocation(pos_calculate=self.pos_calculate)
        # value.from_javalang_node(value_node)
        value.from_node(value_node)
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
