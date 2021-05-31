
import parso
from ContentAnalyzer import KeyValuePair, LineColumnLocation

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

def is_atom_expr(node, i=None):
    if i is not None:
        return node.children[i].type == "atom_expr"
    return node.type == "atom_expr"

def value_equals(node, value, i=None):
    if i is not None:
        return node.children[i].value == value
    return node.value == value

def length_equals(node, value):
    return len(node.children) == value

def is_string_key_value_pair(node):
    if not length_equals(node, 3):
        return False
    if not is_string(node, i=2):
        return False
    if is_name(node, 0) and value_equals(node, "=", 1):
        return True
    elif is_atom_expr(node, i=0):
        key = get_end_node(node, i=0)
        if key is not None:
            # print("expr_stmt with atom_expr kvp: '%s' => '%s'" % (key.value, node.children[2].value)) 
            # value = node.children[2]
            return True
        else:
            # print("expr_stmt with atom_expr kvp: get_text(): '%s' => '%s'" % (node.children[0].value, get_text(node.children[2])))
            return False
    else:
        # print("expr_stmt kvp: get_text(): '%s' => '%s'" % (node.children[0].value, get_text(node.children[2])))
            return False

    raise RuntimeError("Could not make a decision for node '%s'" % (node))

def get_text(node):

    # Return own value
    if hasattr(node, 'value'):
        return node.value

    # No children and no value
    if not hasattr(node, 'children'):
        return

    # Get text value of each node if it has
    # the value prop otherwise recurse into
    # ourselves to get the text value of its children
    values = []
    for n in node.children:
        if not hasattr(n, 'value'):
            value = get_text(n)
        else:
            value = n.value
        values.append(value)

    # text = "".join(values)
    return "".join(values)

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

class Visitor():
    """Visitor"""

    def __init__(self):
        self.matches = []

    def get_matches(self):
        return self.matches.copy()

    def make_node_key_value_pair(self, node, key=0, value=2):
        key_node = node.children[key]
        if is_atom_expr(key_node):
            key_node = get_end_node(key_node)
        value_node = node.children[value]
        return self.make_key_value_pair(key_node, value_node)

    def make_key_value_pair(self, key_node, value_node):
        key = LineColumnLocation(parser_node=key_node)
        value = LineColumnLocation(parser_node=value_node)
        kvp = KeyValuePair(key=key, value=value)
        self.matches.append(kvp)
        return kvp

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
            else:
                key = None
                value = None

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

    def visit_with_stmt(self, node, ctx):
        # print("with_stmt: %s" % (node))
        pass

    def visit_keyword(self, node, ctx):
        # print("keyword: %s" % (node))
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
            'with_stmt': self.visit_with_stmt,
            'keyword': self.visit_keyword,
            'param': self.visit_param,
        }

    def accept(self, node):
        self.visitor = node
        self.visit(self.code)

    def visit(self, node, ctx=None):
        if not hasattr(node, 'children'):
            return
        for n in node.children:
            if n.type in self.map_visit:
                self.map_visit[n.type](n, node)
            else:
                continue

    def visit_expr_stmt(self, node, ctx):
        if self.visitor.visit_expr_stmt(node, ctx) is not None:
            self.visit(node)

    def visit_argument(self, node, ctx):
        if self.visitor.visit_argument(node, ctx) is not None:
            self.visit(node)

    def visit_param(self, node, ctx):
        if self.visitor.visit_param(node, ctx) is not None:
            self.visit(node)

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

    def visit_with_stmt(self, node, ctx):
        self.visitor.visit_with_stmt(node, ctx)
        self.visit(node)

    def visit_keyword(self, node, ctx):
        self.visitor.visit_keyword(node, ctx)
        self.visit(node)

def main():
    """Main."""

    import sys
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "./antlr/python/samples/sample8.py"
    with open(filename, 'r', encoding='utf-8') as f:
        source = f.read()

    code = parso.parse(source)
    w = Walker(code)
    v = Visitor()
    w.accept(v)
    matches = v.get_matches()
    for n in matches:
        print(n)
    # print(matches)
    # print("breakpoint")

if __name__ == "__main__":
    main()
