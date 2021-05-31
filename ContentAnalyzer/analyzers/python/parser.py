"""parser"""

import logging
from typing import List
import attr
import parso
from ContentAnalyzer import LineColumnLocation
from ContentAnalyzer.base import KeyValuePair, PosCalculate


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

# def get_last_trailer_value(node):

#     value = None
#     # if is_trailer(node):
#     #     if length_equals(node, 3):
#     #         value = node.children[1]
#     #     else:
#     #         value = node.children[0]

#     for n in node.children:
#         if check_all_children_type(n, is_trailer):
#             # We have children with trailer, need to check those
#             trailer_child = get_last_trailer_value(n)
#             if not check_all_children_type(trailer_child, is_trailer):
#                 # No children trailers, this is the value!
#                 value = trailer_child
#         else:
#             # No children that is trailer, this is the value!
#             value = node

#     return value

def get_text(node, joiner=""):

    # Return own value
    if hasattr(node, 'value'):
        return node.value

    # No children and no value
    if not hasattr(node, 'children'):
        return

    # Get text value of each node if it has
    # the value prop otherwise recurse into
    # ourselves to get the text value of its children
    # values = []
    # for n in node.children:
    #     if not hasattr(n, 'value'):
    #         value = get_text(n)
    #     else:
    #         value = n.value
    #     values.append(value)

    # # text = "".join(values)
    # return joiner.join(values)
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

class NodeWrapper:
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


class Visitor():
    """Visitor"""

    def __init__(self, text: str = None):
        self.matches = []
        self.comments = []
        self.pos_calculate = PosCalculate(text=text)

        self.logger = logging.getLogger(self.__class__.__name__)

    def get_matches(self) -> List[KeyValuePair]:
        return self.matches.copy()

    def get_comments(self) -> List[LineColumnLocation]:
        return self.comments.copy()

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
        key.from_parso_node(key_node)
        # key.from_node(key_node)
        value = LineColumnLocation(pos_calculate=self.pos_calculate)
        value.from_parso_node(value_node)
        # value.from_node(value_node)
        kvp = KeyValuePair(key=key, value=value)
        self.matches.append(kvp)
        return kvp

    def add_comment(self, node) -> None:
        comment = LineColumnLocation(pos_calculate=self.pos_calculate)
        comment.from_parso_node(node, comment=True)
        # comment.from_node(node, comment=True)
        self.comments.append(comment)

    def visit(self, node, ctx):
        pass

    def visit_expr_stmt(self, node, ctx):
        # print("expr_stmt: %s" % (node))
        if is_string_key_value_pair(node):
            self.make_node_key_value_pair(node, key=0, value=2)
        return True

    def visit_argument(self, node, ctx):
        # print("argument: %s" % (node))
        if is_string_key_value_pair(node):
            self.make_node_key_value_pair(node, key=0, value=2)
        return True

    def visit_param(self, node, ctx):
        # print("param: %s" % (node))
        if is_string_key_value_pair(node):
            self.make_node_key_value_pair(node, key=0, value=2)
        return True

    def visit_comparison(self, node, ctx):
        # print("comparison: %s" % (node))
        if is_string_key_value_pair(node):
            self.make_node_key_value_pair(node, key=0, value=2)

    def visit_dictorsetmaker(self, node, ctx):
        # print("dictorsetmaker: %s" % (node))
        key = None
        value = None
        for n in node.children:
            if is_string(n) and key is None:
                key = n
            elif is_operator(n) and n.value == ':' and key is not None:
                pass
            elif is_string(n) and key is not None:
                value = n
                self.make_key_value_pair(key, value)
                # print("dictorsetmaker kvp: '%s' => '%s'" % (key.value, value.value))
            elif is_term(n) and check_all_children_type(n, is_string) and key is not None:
                value = n
                self.make_key_value_pair(key, value)
            else:
                key = None
                value = None

    def visit_comment(self, node, ctx):
        # print("comment: %s" % (node.prefix))
        if hasattr(node, 'prefix') and node.prefix is not None:
            if '#' in node.prefix:
                self.add_comment(node)
        return

    def visit_name(self, node, ctx):
        # print("name: %s" % (node))
        pass

    def visit_funcdef(self, node, ctx):
        # print("funcdef: %s" % (node))
        pass

    def visit_parameters(self, node, ctx):
        # print("parameters: %s" % (node))
        pass

    def visit_atom_expr(self, node, ctx):
        # print("atom_expr: %s" % (node))
        pass

    def visit_trailer(self, node, ctx):
        # print("trailer: %s" % (node))
        pass

    def visit_simple_stmt(self, node, ctx):
        # print("simple_stmt: %s" % (node))
        pass

    def visit_string(self, node, ctx):
        # print("string: %s" % (node))
        pass

    def visit_suite(self, node, ctx):
        # print("suite: %s" % (node))
        pass

    def visit_arith_expr(self, node, ctx):
        # print("arith_expr: %s" % (node))
        pass

    def visit_arglist(self, node, ctx):
        # print("arglist: %s" % (node))
        pass

    def visit_if_stmt(self, node, ctx):
        # print("if_stmt: %s" % (node))
        pass

    def visit_while(self, node, ctx):
        # print("while: %s" % (node))
        pass

    def visit_atom(self, node, ctx):
        # print("atom: %s" % (node))
        pass

    def visit_with_item(self, node, ctx):
        # print("with_item: %s" % (node))
        pass

    def visit_keyword(self, node, ctx):
        # print("keyword: %s" % (node))
        pass

    def visit_classdef(self, node, ctx):
        # print("classdef: %s" % (node))
        pass

    def visit_testlist_comp(self, node, ctx):
        # print("testlist_comp: %s" % (node))
        pass

    def visit_testlist_star_expr(self, node, ctx):
        # print("testlist_star_expr: %s" % (node))
        pass

    def visit_return_stmt(self, node, ctx):
        # print("return_stmt: %s" % (node))
        pass

    def visit_for_stmt(self, node, ctx):
        # print("for_stmt: %s" % (node))
        pass

    def visit_and_test(self, node, ctx):
        # print("and_test: %s" % (node))
        pass

    def visit_or_test(self, node, ctx):
        # print("or_test: %s" % (node))
        pass

    def visit_not_test(self, node, ctx):
        # print("not_test: %s" % (node))
        pass

    def visit_factor(self, node, ctx):
        # print("factor: %s" % (node))
        pass

    def visit_comp_for(self, node, ctx):
        # print("comp_for: %s" % (node))
        pass

    def visit_subscript(self, node, ctx):
        # print("subscript: %s" % (node))
        pass

    def visit_comp_op(self, node, ctx):
        # print("comp_op: %s" % (node))
        pass

    def visit_with_stmt(self, node, ctx):
        # print("with_stmt: %s" % (node))
        pass

    def visit_testlist(self, node, ctx):
        # print("testlist: %s" % (node))
        pass

    def visit_comp_if(self, node, ctx):
        # print("comp_if: %s" % (node))
        pass

    def visit_exprlist(self, node, ctx):
        # print("exprlist: %s" % (node))
        pass

    def visit_try_stmt(self, node, ctx):
        # print("try_stmt: %s" % (node))
        pass

    def visit_term(self, node, ctx):
        # print("term: %s" % (node))
        pass

    def visit_async_stmt(self, node, ctx):
        # print("async_stmt: %s" % (node))
        pass

    def visit_except_clause(self, node, ctx):
        # print("except_clause: %s" % (node))
        pass

    def visit_while_stmt(self, node, ctx):
        # print("while_stmt: %s" % (node))
        pass

    def visit_error_node(self, node, ctx):
        # print("error_node: %s" % (node))
        pass

    def visit_decorated(self, node, ctx):
        # print("decorated: %s" % (node))
        pass

    def visit_del_stmt(self, node, ctx):
        # print("del_stmt: %s" % (node))
        pass

    def visit_decorator(self, node, ctx):
        # print("decorator: %s" % (node))
        pass

    def visit_dotted_name(self, node, ctx):
        # print("dotted_name: %s" % (node))
        pass

    def visit_yield_expr(self, node, ctx):
        # print("yield_expr: %s" % (node))
        pass

    def visit_yield_arg(self, node, ctx):
        # print("yield_arg: %s" % (node))
        pass

    def visit_raise_stmt(self, node, ctx):
        # print("raise_stmt: %s" % (node))
        pass

    def visit_test(self, node, ctx):
        # print("test: %s" % (node))
        pass

    def visit_strings(self, node, ctx):
        # print("strings: %s" % (node))
        pass

    def visit_endmarker(self, node, ctx):
        # print("endmarker: %s" % (node))
        pass

class Walker():
    """Walker"""

    def __init__(self, code):
        self.visitor = None
        self.code = code
        self.map_visit = {
            'simple_stmt': self.visit_simple_stmt,
            'expr_stmt': self.visit_expr_stmt,
            'name': self.visit_name,
            'string': self.visit_string,
            'atom_expr': self.visit_atom_expr,
            'funcdef': self.visit_funcdef,
            'parameters': self.visit_parameters,
            'trailer': self.visit_trailer,
            'suite': self.visit_suite,
            'arith_expr': self.visit_arith_expr,
            'argument': self.visit_argument,
            'dictorsetmaker': self.visit_dictorsetmaker,
            'arglist': self.visit_arglist,
            'if_stmt': self.visit_if_stmt,
            'while': self.visit_while,
            'atom': self.visit_atom,
            'with_item': self.visit_with_item,
            'keyword': self.visit_keyword,
            'param': self.visit_param,
            'classdef': self.visit_classdef,
            'testlist_comp': self.visit_testlist_comp,
            'testlist_star_expr': self.visit_testlist_star_expr,
            'comparison': self.visit_comparison,
            'return_stmt': self.visit_return_stmt,
            'for_stmt': self.visit_for_stmt,
            'and_test': self.visit_and_test,
            'or_test': self.visit_or_test,
            'not_test': self.visit_not_test,
            'factor': self.visit_factor,
            'comp_for': self.visit_comp_for,
            'subscript': self.visit_subscript,
            'comp_op': self.visit_comp_op,
            'with_stmt': self.visit_with_stmt,
            'testlist': self.visit_testlist,
            'comp_if': self.visit_comp_if,
            'exprlist': self.visit_exprlist,
            'try_stmt': self.visit_try_stmt,
            'term': self.visit_term,
            'async_stmt': self.visit_async_stmt,
            'except_clause': self.visit_except_clause,
            'while_stmt': self.visit_while_stmt,
            'error_node': self.visit_error_node,
            'decorated': self.visit_decorated,
            'del_stmt': self.visit_del_stmt,
            'decorator': self.visit_decorator,
            'dotted_name': self.visit_dotted_name,
            'yield_expr': self.visit_yield_expr,
            'yield_arg': self.visit_yield_arg,
            'raise_stmt': self.visit_raise_stmt,
            'test': self.visit_test,
            'strings': self.visit_strings,
            'endmarker': self.visit_endmarker,
        }
        self.ignore = [
            'newline',
            'operator',
            'number',
            'import_from',
            'import_name',
        ]

    def accept(self, node):
        self.visitor = node
        self.visit(self.code)

    def visit(self, node, ctx=None):
        if not hasattr(node, 'children'):
            return
        for n in node.children:
            if n.type in self.ignore:
                continue
            if n.type in self.map_visit:
                self.map_visit[n.type](n, node)
            else:
                print("", end='')
                continue
            if hasattr(n, 'prefix'):
                self.visit_comment(n, node)

    def visit_expr_stmt(self, node, ctx):
        if self.visitor.visit_expr_stmt(node, ctx) is not None:
            self.visit(node)
        else:
            return

    def visit_argument(self, node, ctx):
        if self.visitor.visit_argument(node, ctx) is not None:
            self.visit(node)
        else:
            return

    def visit_param(self, node, ctx):
        if self.visitor.visit_param(node, ctx) is not None:
            self.visit(node)
        else:
            return

    def visit_simple_stmt(self, node, ctx):
        self.visitor.visit_simple_stmt(node, ctx)
        self.visit(node)

    def visit_name(self, node, ctx):
        self.visitor.visit_name(node, ctx)
        self.visit(node)

    def visit_string(self, node, ctx):
        self.visitor.visit_string(node, ctx)
        self.visit(node)

    def visit_atom_expr(self, node, ctx):
        self.visitor.visit_atom_expr(node, ctx)
        self.visit(node)

    def visit_funcdef(self, node, ctx):
        self.visitor.visit_funcdef(node, ctx)
        self.visit(node)

    def visit_parameters(self, node, ctx):
        self.visitor.visit_parameters(node, ctx)
        self.visit(node)

    def visit_trailer(self, node, ctx):
        self.visitor.visit_trailer(node, ctx)
        self.visit(node)

    def visit_suite(self, node, ctx):
        self.visitor.visit_suite(node, ctx)
        self.visit(node)

    def visit_arith_expr(self, node, ctx):
        self.visitor.visit_arith_expr(node, ctx)
        self.visit(node)

    def visit_dictorsetmaker(self, node, ctx):
        self.visitor.visit_dictorsetmaker(node, ctx)
        self.visit(node)

    def visit_arglist(self, node, ctx):
        self.visitor.visit_arglist(node, ctx)
        self.visit(node)

    def visit_if_stmt(self, node, ctx):
        self.visitor.visit_if_stmt(node, ctx)
        self.visit(node)

    def visit_while(self, node, ctx):
        self.visitor.visit_while(node, ctx)
        self.visit(node)

    def visit_atom(self, node, ctx):
        self.visitor.visit_atom(node, ctx)
        self.visit(node)

    def visit_with_item(self, node, ctx):
        self.visitor.visit_with_item(node, ctx)
        self.visit(node)

    def visit_keyword(self, node, ctx):
        self.visitor.visit_keyword(node, ctx)
        self.visit(node)

    def visit_classdef(self, node, ctx):
        self.visitor.visit_classdef(node, ctx)
        self.visit(node)

    def visit_testlist_comp(self, node, ctx):
        self.visitor.visit_testlist_comp(node, ctx)
        self.visit(node)

    def visit_testlist_star_expr(self, node, ctx):
        self.visitor.visit_testlist_star_expr(node, ctx)
        self.visit(node)

    def visit_comparison(self, node, ctx):
        self.visitor.visit_comparison(node, ctx)
        self.visit(node)

    def visit_return_stmt(self, node, ctx):
        self.visitor.visit_return_stmt(node, ctx)
        self.visit(node)

    def visit_for_stmt(self, node, ctx):
        self.visitor.visit_for_stmt(node, ctx)
        self.visit(node)

    def visit_and_test(self, node, ctx):
        self.visitor.visit_and_test(node, ctx)
        self.visit(node)

    def visit_or_test(self, node, ctx):
        self.visitor.visit_or_test(node, ctx)
        self.visit(node)

    def visit_not_test(self, node, ctx):
        self.visitor.visit_not_test(node, ctx)
        self.visit(node)

    def visit_factor(self, node, ctx):
        self.visitor.visit_factor(node, ctx)
        self.visit(node)

    def visit_comp_for(self, node, ctx):
        self.visitor.visit_comp_for(node, ctx)
        self.visit(node)

    def visit_subscript(self, node, ctx):
        self.visitor.visit_subscript(node, ctx)
        self.visit(node)

    def visit_comp_op(self, node, ctx):
        self.visitor.visit_comp_op(node, ctx)
        self.visit(node)

    def visit_with_stmt(self, node, ctx):
        self.visitor.visit_with_stmt(node, ctx)
        self.visit(node)

    def visit_testlist(self, node, ctx):
        self.visitor.visit_testlist(node, ctx)
        self.visit(node)

    def visit_comp_if(self, node, ctx):
        self.visitor.visit_comp_if(node, ctx)
        self.visit(node)

    def visit_exprlist(self, node, ctx):
        self.visitor.visit_exprlist(node, ctx)
        self.visit(node)

    def visit_try_stmt(self, node, ctx):
        self.visitor.visit_try_stmt(node, ctx)
        self.visit(node)

    def visit_term(self, node, ctx):
        self.visitor.visit_term(node, ctx)
        self.visit(node)

    def visit_async_stmt(self, node, ctx):
        self.visitor.visit_async_stmt(node, ctx)
        self.visit(node)

    def visit_except_clause(self, node, ctx):
        self.visitor.visit_except_clause(node, ctx)
        self.visit(node)

    def visit_while_stmt(self, node, ctx):
        self.visitor.visit_while_stmt(node, ctx)
        self.visit(node)

    def visit_error_node(self, node, ctx):
        self.visitor.visit_error_node(node, ctx)
        self.visit(node)

    def visit_decorated(self, node, ctx):
        self.visitor.visit_decorated(node, ctx)
        self.visit(node)

    def visit_del_stmt(self, node, ctx):
        self.visitor.visit_del_stmt(node, ctx)
        self.visit(node)

    def visit_decorator(self, node, ctx):
        self.visitor.visit_decorator(node, ctx)
        self.visit(node)

    def visit_dotted_name(self, node, ctx):
        self.visitor.visit_dotted_name(node, ctx)
        self.visit(node)

    def visit_yield_expr(self, node, ctx):
        self.visitor.visit_yield_expr(node, ctx)
        self.visit(node)

    def visit_yield_arg(self, node, ctx):
        self.visitor.visit_yield_arg(node, ctx)
        self.visit(node)

    def visit_raise_stmt(self, node, ctx):
        self.visitor.visit_raise_stmt(node, ctx)
        self.visit(node)

    def visit_test(self, node, ctx):
        self.visitor.visit_test(node, ctx)
        self.visit(node)

    def visit_strings(self, node, ctx):
        self.visitor.visit_strings(node, ctx)
        self.visit(node)

    def visit_endmarker(self, node, ctx):
        self.visitor.visit_endmarker(node, ctx)
        self.visit(node)

    def visit_comment(self, node, ctx):
        self.visitor.visit_comment(node, ctx)
        self.visit(node)
