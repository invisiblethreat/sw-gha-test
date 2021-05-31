"""Php Visitor"""

from typing import Any, Dict, List, Tuple, Union, TYPE_CHECKING
from ContentAnalyzer.analyzers.php.phpparser import ast
from ContentAnalyzer.analyzers.php.phpparser.ast import Node

from ContentAnalyzer import KeyValuePair, LineColumnLocation
from ContentAnalyzer.base import PosCalculate

if TYPE_CHECKING:
    Node.node: Node = None
    Node.params: List[ast.Parameter] = None
    Node.value: Any = None
    Node.name: str = None

def _flatten_list(item: List[Any]) -> List[Any]:

    children = list()
    for thing in item:
        if isinstance(thing, list):
            children.extend(_flatten_list(thing))
        else:
            children.append(thing)

    return children

class Visitor:
    """PHP Visitor.

    Attributes:

        tree (List): Tree that was visited.
    """

    def __init__(self):

        self.tree = None

    def visit(self, tree: List) -> None:
        """Visit a phply Tree.

        Args:

            tree (Node): php tree to visit.

        Returns:

            None.
        """
        self.tree = tree

        for child in tree:
            self.walk(child, None)


    def walk(self, node: Node, ctx: Union[Node, None]) -> None:
        """Walk a node and it's children.

        Walk a node and the children of whatever node is returned to the visiting method.

        Args:

            node (Node): phply parser node.
            ctx (Union[Node, Tuple]): Parent context or None.

        Returns:

            None.
        """
        if isinstance(node, ast.Node):
            pass
        elif isinstance(node, list):
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
            for field in node.fields:
                child = getattr(node, field)
                self.walk(child, new_node)

    def visit_InlineHTML(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Block(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Assignment(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_ListAssignment(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_New(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Clone(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Break(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Continue(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Return(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Yield(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Global(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Static(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Echo(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Print(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Unset(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Try(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Catch(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Finally(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Throw(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Declare(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Directive(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Function(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Method(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Closure(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Class(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Trait(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_ClassConstants(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_ClassConstant(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_ClassVariables(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_ClassVariable(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Interface(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_AssignOp(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_BinaryOp(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_UnaryOp(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_TernaryOp(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_PreIncDecOp(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_PostIncDecOp(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Cast(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_IsSet(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Empty(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Eval(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Include(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Require(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Exit(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Silence(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_MagicConstant(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Constant(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Variable(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_StaticVariable(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_LexicalVariable(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_FormalParameter(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Parameter(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_FunctionCall(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Array(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_ArrayElement(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_ArrayOffset(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_StringOffset(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_ObjectProperty(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_StaticProperty(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_MethodCall(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_StaticMethodCall(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_If(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_ElseIf(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Else(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_While(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_DoWhile(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_For(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Foreach(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_ForeachVariable(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Switch(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Case(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Default(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Namespace(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_UseDeclarations(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_UseDeclaration(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_ConstantDeclarations(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_ConstantDeclaration(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_TraitUse(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_TraitModifier(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_ExprScalar(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Scalar(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


    def visit_Body(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        return node


class PhpVisitor(Visitor):
    """PhpVisitor"""


    def __init__(self, text: str = None):
        super().__init__()
        self.text = text
        self.contexts: List[Node] = list()
        self.keys: List[Node] = list()
        self.key: Node = None
        self.value: Node = None

        self.matches: List[Dict] = list()


    def get_matches(self) -> List[Dict]:
        """Get list of KeyValuePairs.

        Returns:

            list: List of KeyValuePair.
        """
        return self.matches.copy()


    def set_state(self, node: Node):
        """Set and maintain state for key/value pairs.

        Args:

            node (Node): Node to add to state.

        Returns:

            None.
        """
        kind = node.__class__.__name__

        if kind == "Assignment":
            # TODO: Figure out how to do $variable['AWS_SECRET_KEY'] parsing
            if node.node.__class__.__name__ != "ArrayOffset":
                self.key = node.node

        elif kind == "ClassVariable":
            self.key = node.node

        elif kind == "Print":
            # Need to visit child nodes so store our "state"
            # as the last MethodInovcation so that added
            # Literals match up properly.
            node.name = "print"
            self.contexts.append(node)

            # Store current key (even if it is None) in
            # self.keys to preserve state when pop ourselves
            # from stack.
            self.keys.append(self.key)
            self.key = None

            # for child in node.fields:
            self.walk(node.node, node)

            self.key = self.keys.pop()
            self.contexts.pop()

        elif kind in ("MethodCall", "FunctionCall"):
            # Need to visit child nodes so store our "state"
            # as the last MethodInovcation so that added
            # Literals match up properly.
            self.contexts.append(node)

            # Store current key (even if it is None) in
            # self.keys to preserve state when pop ourselves
            # from stack.
            self.keys.append(self.key)
            self.key = None

            for child in node.params:
                self.walk(child, node)

            self.key = self.keys.pop()
            self.contexts.pop()

        elif kind == "Scalar":
            if not isinstance(node.value, str):
                return
            if self.contexts:
                # We're iterating on MethodInvocation currently
                # so this Literal belongs to it
                key_node = self.contexts[-1]
                # name = key_node.name
            else:
                if self.key is None:
                    return
                key_node = self.key

            key_kind = key_node.__class__.__name__
            if key_kind == "VariableDeclarator":
                # name = self.key.name
                key_node = self.key

            self.value = node
            value_node = node
            value = self.value.value
            name = key_node.name

            # if value.startswith('"') and value.startswith('"'):
            #     # This is a string so parse it
            #     # self.make_key_value_pair(key_node, value_node)
            # print(name, end=' => ')
            # print(self.value.value)
            # print(f"{self.value.lineno}:{self.value.lexpos} {name} => '{self.value.value}'")
            self.make_key_value_pair(key_node, self.value)
            self.key = None
            self.value = None


    # pylint: disable=line-too-long
    def make_key_value_pair(self, key_node: Node, value_node: Node):
        """Make a KeyValuePair from a pair of EsprimaNodes.

        Args:

            key_node (TypeVar): Key node or possible a string of the key?
            value_node (TypeVar): Value node.

        Returns:

            KeyValuePair: KeyValuePair for nodes.
        """

        key_dict = self._make_node_position_dict(key_node)
        value_dict = self._make_node_position_dict(value_node)
        kvp_dict = self._make_kvp_position_dict(key_dict, value_dict)
        self.matches.append(kvp_dict)
    # pylint: disable=line-too-long

    def _make_node_position_dict(self, node: Node) -> Dict:
        """Make position dict for a token"""

        value = node.value if hasattr(node, 'value') else node.name

        if not isinstance(value, str):
            if value.__class__.__name__ == "Variable":
                value = value.name
            else:
                raise TypeError(f"Don't know how to handle value type '{str(type(value))}'")

        start_pos = node.lexpos + 1
        length = len(value)
        start_column = self._find_column(node)

        position = {
            'start_pos': start_pos,
            'value': value,
            'end_pos': start_pos + length,
            'start_column': start_column,
            'end_column': start_column + length,
            'start_line': node.lineno,
            'end_line': node.lineno,
        }

        return position

    def _make_kvp_position_dict(self, key_dict: Dict, value_dict: Dict) -> Dict:
        """Make kvp position dict"""

        position = {
            'key': key_dict['value'],
            'value': value_dict['value'],
            'start_pos': value_dict['start_pos'],
            'end_pos': value_dict['end_pos'],
            'start_line': value_dict['start_line'],
            'end_line': value_dict['end_line'],
            'start_column': value_dict['start_column'],
            'end_column': value_dict['end_column'],
        }
        return position

    def _find_column(self, node: Node) -> int:
        """Find the column for a token"""
        line_start = self.text.rfind('\n', 0, node.lexpos) + 1
        return (node.lexpos - line_start) + 1

    def visit_Assignment(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        self.set_state(node)
        return node

    # def visit_Print(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
    def visit_Print(self, node: Node, ctx: Union[Node, Tuple]) -> None:
        self.set_state(node)
        # return node
        return None

    # def visit_FunctionCall(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
    def visit_FunctionCall(self, node: Node, ctx: Union[Node, Tuple]) -> None:
        self.set_state(node)
        # return node
        return None

    def visit_Scalar(self, node: Node, ctx: Union[Node, Tuple]) -> Union[Node, None]:
        self.set_state(node)
        return node
