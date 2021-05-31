"""parser"""

import logging
from typing import List, Tuple, Union

import parso

from ContentAnalyzer import KeyValuePair, LineColumnLocation
from ContentAnalyzer.base import PosCalculate

Node = 'Node'

def is_trailer(node, i=None):
    if i is not None:
        return node.children[i].type == "trailer"
    return node.type == "trailer"

def is_name(node, i=None):
    if i is not None:
        return node.children[i].type == "name"
    return node.type == "name"

def is_operator(node, i=None):
    if i is not None:
        return node.children[i].type == "operator"
    return node.type == "operator"

def is_string(node, i=None):
    if i is not None:
        return node.children[i].type == "string"
    return node.type == "string"

def is_atom(node, i=None):
    if i is not None:
        return node.children[i].type == "atom"
    return node.type == "atom"

def is_atom_expr(node, i=None):
    if i is not None:
        return node.children[i].type == "atom_expr"
    return node.type == "atom_expr"

def is_term(node, i=None):
    if i is not None:
        return node.children[i].type == "term"
    return node.type == "term"

def is_arith_expr(node, i=None):
    if i is not None:
        return node.children[i].type == "arith_expr"
    return node.type == "arith_expr"

def is_or_test(node, i=None):
    if i is not None:
        return node.children[i].type == "or_test"
    return node.type == "or_test"

def is_dictorsetmaker(node, i=None):
    if i is not None:
        return node.children[i].type == "dictorsetmaker"
    return node.type == "dictorsetmaker"

def value_equals(node, value, i=None):
    if i is not None:
        if not hasattr(node.children[i], 'value'):
            return False
        return node.children[i].value == value
    return node.value == value

def length_equals(node, value):
    if not hasattr(node, 'children'):
        return False
    return len(node.children) == value

def is_string_key_value_pair(node):
    if not length_equals(node, 3):
        return False
    # if not is_string(node, i=2):
    #     return False
    if is_name(node, 0) and value_equals(node, "=", 1):
        if is_string(node, i=2):
            return True
        elif is_term(node, i=2):
            # Matches like: var = "some string %s" % value
            return check_all_children_type(node.children[2], is_string)
        elif is_atom(node, i=2):
            return check_value_for_dictorsetmaker(node.children[2])
        else:
            return False
    elif is_atom_expr(node, i=0) and value_equals(node, "=", 1):
        # Will match when left side is like thing.prop
        key = get_end_node(node, i=0)
        if key is not None:
            # print("expr_stmt with atom_expr kvp: '%s' => '%s'" % (key.value, node.children[2].value))
            value = node.children[2]
            # return True
            # Check value to see if its middle child node is a dictorsetmaker
            if is_atom(node, i=2):
                return check_value_for_dictorsetmaker(node.children[2])
            elif is_atom_expr(node, i=2):
                return False
            elif length_equals(value, 2) and is_name(value, i=0) and value_equals(node, "int", i=0):
                # Match int(<stmt>)
                return False
            return check_all_children_type(node.children[2], is_string)
        else:
            # print("expr_stmt with atom_expr kvp: get_text(): '%s' => '%s'" % (node.children[0].value, get_text(node.children[2])))
            return False
    else:
        # print("expr_stmt kvp: get_text(): '%s' => '%s'" % (node.children[0].value, get_text(node.children[2])))
        return False

    raise RuntimeError("Could not make a decision for node '%s'" % (node))

def check_value_for_dictorsetmaker(node):
    if length_equals(node, 3):
        if is_dictorsetmaker(node, i=2):
            # Is a dict or set so ignore
            return True
    return False

def check_all_children_type(node, func):

    # Return own value
    if func(node):
        return True
    elif not hasattr(node, 'children'):
        return False

    for n in node.children:
        if check_all_children_type(n, func):
            return True

    return False


def get_text(node, joiner=""):

    # Return own value
    if hasattr(node, 'value'):
        return node.value

    # No children and no value
    if not hasattr(node, 'children'):
        return

    text = node.get_code().strip()
    return text

def get_end_node(parent, i=None):
    if i is not None:
        node = parent.children[i]
    else:
        node = parent

    # We are Name, return it
    if is_name(node):
        return node
    elif is_trailer(node):
        # Check for prop in blah.prop
        if is_operator(node, i=0) and value_equals(node, ".", i=0):
            return node.children[1]
        # Check for prop in blah['prop']
        elif length_equals(node, 3):
            if is_operator(node, i=0) and is_operator(node, i=2):
                if value_equals(node, "[", i=0) and value_equals(node, "]", i=2):
                    return node.children[1]

    elif hasattr(node, 'children'):
        return get_end_node(node, i=-1)
    return

class NodeWrapper():
    """NodeWrapper."""

    def __init__(self, node):
        self.node = node

    @property
    def value(self):
        return get_text(self.node, joiner=" ")

    @property
    def type(self):
        return self.node.type

    @property
    def end_pos(self):
        return self.node.end_pos

    @property
    def start_pos(self):
        return self.node.start_pos

    @property
    def parent(self):
        return self.node.parent


class Visitor:
    """Visitor"""


    def __init__(self):

        self.tree = None


    def visit(self, tree: 'Node') -> None:
        """Visit a javalang Tree.

        Args:

            tree (Node): javalang tree to visit.

        Returns:

            None.
        """
        self.tree = tree

        for child in tree.children:
            self.walk(child, None)


    def walk(self, node: 'Node', ctx: Union['Node', Tuple]) -> None:
        """Walk a node and it's children.

        Walk a node and the children of whatever node is returned to the visiting method.

        Args:

            node (Node): Java parser node.
            ctx (Union[Node, Tuple]): Parent context or None.

        Returns:

            None.
        """

        method_name = f"visit_{node.type}"
        method = getattr(self, method_name)

        new_node = method(node, ctx)

        if not hasattr(new_node, 'children'):
            return

        for child in node.children:
            self.walk(child, new_node)


    # pylint: disable=unused-argument,missing-docstring,line-too-long,no-self-use
    def visit_expr_stmt(self, node, ctx):
        print("", end='')
        return node

    def visit_operator(self, node, ctx):
        print("", end='')
        return node

    def visit_argument(self, node, ctx):
        print("", end='')
        return node

    def visit_newline(self, node, ctx):
        print("", end='')
        return node

    def visit_import_name(self, node, ctx):
        print("", end='')
        return node

    def visit_import_from(self, node, ctx):
        print("", end='')
        return node

    def visit_import_as_name(self, node, ctx):
        print("", end='')
        return node

    def visit_param(self, node, ctx):
        print("", end='')
        return node

    def visit_comparison(self, node, ctx):
        print("", end='')
        return node

    def visit_dictorsetmaker(self, node, ctx):
        print("", end='')
        return node

    def visit_comment(self, node, ctx):
        print("", end='')
        return node

    def visit_name(self, node, ctx):
        print("", end='')
        return node

    def visit_number(self, node, ctx):
        print("", end='')
        return node

    def visit_funcdef(self, node, ctx):
        print("", end='')
        return node

    def visit_parameters(self, node, ctx):
        print("", end='')
        return node

    def visit_atom_expr(self, node, ctx):
        print("", end='')
        return node

    def visit_trailer(self, node, ctx):
        print("", end='')
        return node

    def visit_simple_stmt(self, node, ctx):
        print("", end='')
        return node

    def visit_string(self, node, ctx):
        print("", end='')
        return node

    def visit_suite(self, node, ctx):
        print("", end='')
        return node

    def visit_arith_expr(self, node, ctx):
        print("", end='')
        return node

    def visit_arglist(self, node, ctx):
        print("", end='')
        return node

    def visit_if_stmt(self, node, ctx):
        print("", end='')
        return node

    def visit_while(self, node, ctx):
        print("", end='')
        return node

    def visit_atom(self, node, ctx):
        print("", end='')
        return node

    def visit_with_item(self, node, ctx):
        print("", end='')
        return node

    def visit_keyword(self, node, ctx):
        print("", end='')
        return node

    def visit_classdef(self, node, ctx):
        print("", end='')
        return node

    def visit_testlist_comp(self, node, ctx):
        print("", end='')
        return node

    def visit_testlist_star_expr(self, node, ctx):
        print("", end='')
        return node

    def visit_return_stmt(self, node, ctx):
        print("", end='')
        return node

    def visit_for_stmt(self, node, ctx):
        print("", end='')
        return node

    def visit_and_test(self, node, ctx):
        print("", end='')
        return node

    def visit_or_test(self, node, ctx):
        print("", end='')
        return node

    def visit_not_test(self, node, ctx):
        print("", end='')
        return node

    def visit_factor(self, node, ctx):
        print("", end='')
        return node

    def visit_comp_for(self, node, ctx):
        print("", end='')
        return node

    def visit_subscript(self, node, ctx):
        print("", end='')
        return node

    def visit_comp_op(self, node, ctx):
        print("", end='')
        return node

    def visit_with_stmt(self, node, ctx):
        print("", end='')
        return node

    def visit_testlist(self, node, ctx):
        print("", end='')
        return node

    def visit_comp_if(self, node, ctx):
        print("", end='')
        return node

    def visit_exprlist(self, node, ctx):
        print("", end='')
        return node

    def visit_try_stmt(self, node, ctx):
        print("", end='')
        return node

    def visit_term(self, node, ctx):
        print("", end='')
        return node

    def visit_async_stmt(self, node, ctx):
        print("", end='')
        return node

    def visit_except_clause(self, node, ctx):
        print("", end='')
        return node

    def visit_while_stmt(self, node, ctx):
        print("", end='')
        return node

    def visit_error_node(self, node, ctx):
        print("", end='')
        return node

    def visit_decorated(self, node, ctx):
        print("", end='')
        return node

    def visit_del_stmt(self, node, ctx):
        print("", end='')
        return node

    def visit_decorator(self, node, ctx):
        print("", end='')
        return node

    def visit_dotted_name(self, node, ctx):
        print("", end='')
        return node

    def visit_yield_expr(self, node, ctx):
        print("", end='')
        return node

    def visit_yield_arg(self, node, ctx):
        print("", end='')
        return node

    def visit_raise_stmt(self, node, ctx):
        print("", end='')
        return node

    def visit_test(self, node, ctx):
        print("", end='')
        return node

    def visit_strings(self, node, ctx):
        print("", end='')
        return node

    def visit_endmarker(self, node, ctx):
        print("", end='')
        return node

    # pylint: enable=unused-argument,missing-docstring,line-too-long,no-self-use


class PythonVisitor(Visitor):
    """PythonVisitor"""

    def __init__(self, text: str = None):
        super().__init__()
        self.pos_calculate = PosCalculate(text=text)
        self.contexts = []
        self.keys = []
        self.key = None
        self.value = None

        self.matches = []

        self.logger = logging.getLogger(self.__class__.__name__)


    def get_matches(self) -> List[KeyValuePair]:
        return self.matches.copy()


    def make_node_key_value_pair(self, node, key=0, value=2) -> KeyValuePair:
        try:
            key_node = node.children[key]
            if is_atom_expr(key_node):
                key_node = get_end_node(key_node)
            value_node = node.children[value]
            if is_term(value_node) or is_arith_expr(value_node) or is_or_test(value_node):
                value_node = NodeWrapper(value_node)
            return self.make_key_value_pair(key_node, value_node)
        except Exception:
            self.logger.exception("Exception while trying to create key/value pair for '%s'" % (node.get_code()), exc_info=True)
            return


    def make_key_value_pair(self, key_node, value_node) -> KeyValuePair:
        key = LineColumnLocation(pos_calculate=self.pos_calculate)
        # key.from_parso_node(key_node)
        key.from_node(key_node)
        value = LineColumnLocation(pos_calculate=self.pos_calculate)
        # value.from_parso_node(value_node)
        value.from_node(value_node)
        kvp = KeyValuePair(key=key, value=value)
        self.matches.append(kvp)
        return kvp

    def set_state(self, node: 'Node') -> None:
        """Set and maintain state for key/value pairs.

        Args:

            node (Node): Node to add to state.

        Returns:

            None.
        """
        kind = node.type

        if kind == "name":
            self.key = node

        elif kind == "MethodInvocation":
            # TODO: Add dictorsetmaker and other tokens here
            # to change context as the key/value assignment
            # can move from name -> string to string -> name

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

        elif kind == "string":
            # TODO: Change key/value assignment based upon current context.
            # Context change to dictorsetmaker and possible others can change
            # the key/value assignment from name -> string to string -> name
            if self.contexts:
                # We're iterating on MethodInvocation currently
                # so this Literal belongs to it
                key_node = self.contexts[-1]
                name = key_node.value
            else:
                if self.key is None:
                    return

            key_kind = self.key.type
            if key_kind == "name":
                name = self.key.value
                key_node = self.key

            self.value = node
            value_node = node
            value = self.value.value

            if value.startswith('"') and value.startswith('"'):
                # This is a string so parse it
                self.make_key_value_pair(key_node, value_node)
                # print(name, end=' => ')
                # print(self.value.value)
            print(name, end=' => ')
            print(self.value.value)
            self.key = None
            self.value = None


    def visit_name(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        self.set_state(node)
        print("", end='')
        return node


    def visit_string(self, node: Node, ctx: Union[Node, None]) -> Union[Node, None]:
        self.set_state(node)
        print("", end='')
        return node


def read_contents(filename: str) -> str:
    """Read contents of file"""

    f = open(filename, 'r', encoding='utf-8')
    content = f.read()
    f.close()
    return content


def main():
    """Main."""

    filename = "tests/data/python/sample5.py"
    content = read_contents(filename)

    tree = parso.parse(content)

    visitor = PythonVisitor(text=content)
    visitor.visit(tree)

    print("", end='')


if __name__ == "__main__":
    main()
