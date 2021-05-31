import ast


def is_Attribute(node):
    return isinstance(node, ast.Attribute)

def is_Str(node):
    return isinstance(node, ast.Str)

def is_Num(node):
    return isinstance(node, ast.Num)

def is_Name(node):
    return isinstance(node, ast.Name)

def is_Dict(node):
    return isinstance(node, ast.Dict)

def is_List(node):
    return isinstance(node, ast.List)

def is_Call(node):
    return isinstance(node, ast.Call)

def is_arg(node):
    return isinstance(node, ast.arg)

def is_keyword(node):
    return isinstance(node, ast.keyword)

def is_BinOp(node):
    return isinstance(node, ast.BinOp)

def is_Subscript(node):
    return isinstance(node, ast.Subscript)

def is_Slice(node):
    return isinstance(node, ast.Slice)

def is_Add(node):
    return isinstance(node, ast.Add)

def get_text(node):
    if is_Str(node):
        value = node.s
    elif is_Attribute(node):
        value = node.attr
    elif is_arg(node):
        value = node.arg
    elif is_Name(node):
        value = node.id
    elif is_keyword(node):
        value = node.arg
    elif is_Add(node):
        value = "+"
    elif is_Subscript(node):
        return
    elif is_BinOp(node):
        value = get_text(node.op)
    elif is_Call(node):
        value = "!!TODO: FIX THIS Call()!!"
    else:
        print("**get_text() don't know %s" % type(node).__name__)
        return
    return value

def get_pos(node):
    if is_Str(node):
        value = node.s
    elif is_Attribute(node):
        value = node.attr
    elif is_arg(node):
        value = node.arg
    elif is_Name(node):
        value = node.id
    elif is_keyword(node):
        # print("keyword '%s' @ ?" % (node.arg))
        value = node.arg
        return
    elif is_Subscript(node):
        get_pos(node.slice.value)
        return
        # print("subscript '%s' @ ?" % (node.arg))
        # return
    # This is for a str
    start_line = node.lineno
    start_column = node.col_offset
    # No value for binop!
    # TODO: Get value for binop
    if is_BinOp(node):
        # print("binop '%s' @ %s, %s -> ?" % (get_text(node), start_line, start_column))
        return
    length = len(value)
    end_column = start_column + length
    # print("'%s' @ %s, %s -> %s" % (value, start_line, start_column, end_column))

def dict_kvp_printer(node):
    paired = zip(node.keys, node.values)
    for k, v in paired:
        if is_Str(k) and is_Str(v):
            print("dict: '%s' => '%s'" % (k.s, v.s))
            # get_pos(k)
            get_pos(k)
            sep_print()

def keyword_kvp_printer(node):
    if not node.keywords:
        return
    for kw in node.keywords:
        if is_Str(kw.value):
            print("keyw: '%s' => '%s'" % (kw.arg, kw.value.s))
            # get_pos(kw)
            get_pos(kw.value)
            sep_print()

def make_kvp(key, value):
    print("'%s' => '%s'" % (key, value))

def sep_print():
    print("=" * 40)

class RecursiveVisitor(ast.NodeVisitor):
    """ example recursive visitor """

    def __init__(self, *args, **kwargs):
        super(RecursiveVisitor, self).__init__()
        self.last_node = None
        self.binop_stack = []
        self.binop_text = None

    def recursive(func):
        """ decorator to make visitor work recursive """
        def wrapper(self, node):
            func(self, node)
            for child in ast.iter_child_nodes(node):
                self.visit(child)
        return wrapper

    def visit_Name(self, node):
        # print(type(node).__name__)
        # print(type(self.last_node).__name__)
        # print(ast.dump(node))
        # print("")
        pass

    @recursive
    def visit_Assign(self, node):
        """ visit a Assign node and visits it recursively"""
        # Need to handle these:
        # Assign(targets=[Subscript(value=Attribute(value=Name(id='os', ctx=Load()), attr='environ', ctx=Load()), slice=Index(value=Str(s='NETSIL_VERSION_NUMBER')), ctx=Store())], value=Name(id='LATEST_VERSION_NUMBER', ctx=Load()))
        # os.environ['NETSIL_VERSION_NUMBER'] = LATEST_VERSION_NUMBER
        #
        # os.environ['BUILD_ENV'] = 'production'
        if not is_Str(node.value) and not is_BinOp(node.value):
            if is_Dict(node.value) or is_List(node.value) or is_Num(node.value) or is_Call(node.value):
                # return
                print("", end='')
                # pass
            elif is_Name(node.value):
                # Seen this happen with:
                # os.environ.get('LATEST_VERSION_NUMBER', failobj='0.2.0')
                print("get() used: %s" % (ast.dump(node)))
                sep_print()
                # return
            else:
                # TODO: Handle these
                # Assign(targets=[Name(id='app_dict', ctx=Store())], value=Subscript(value=Attribute(value=Name(id='self', ctx=Load()), attr='app_index', ctx=Load()), slice=Index(value=Name(id='app_id', ctx=Load())), ctx=Load()))
                # app_dict = self.app_index[app_id]
                # Assign(targets=[Name(id='app_env', ctx=Store())], value=Subscript(value=Subscript(value=Call(func=Attribute(value=Name(id='resp', ctx=Load()), attr='json', ctx=Load()), args=[], keywords=[]), slice=Index(value=Str(s='app')), ctx=Load()), slice=Index(value=Str(s='env')), ctx=Load()))
                # app_env = resp.json()['app']['env']
                # print("Unknown assign::: %s" % (ast.dump(node)))
                # print("lineno: %s" % (node.lineno))
                print("", end='')
            return
        if len(node.targets) == 1:
            target = node.targets[0]
            # TODO: Make is_Num work!
            # TODO: Need to actually get all Key/Value pairs!
            if is_Name(target) and is_Str(node.value):
                print("name: '%s' => '%s'" % (target.id, node.value.s))
            elif is_Attribute(target):
                if is_Str(node.value):
                    print("attr: '%s' => '%s'" % (target.attr, node.value.s))
                elif is_BinOp(node.value):
                    self.custom_BinOp(node.value)
                    # print(ast.dump(node))
                    print("bnop: '%s' => '%s'" % (get_text(target), self.binop_text))
                    self.binop_text = None
                    return
                else:
                    print("unknown attribute target assign: %s" % (ast.dump(node)))
                    sep_print()
                    return
            elif is_BinOp(node.value):
                self.custom_BinOp(node.value)
                # print(ast.dump(node))
                print("bnop: '%s' => '%s'" % (get_text(target), self.binop_text))
                self.binop_text = None
                # TODO: Get 
                sep_print()
                return
            elif is_Subscript(target):
                if is_Str(target.slice.value):
                    print("slce: '%s' => '%s'" % (target.slice.value.s, node.value.s))
                else:
                    print("Unknown slice assign::: %s" % (ast.dump(node)))
                    sep_print()
                    return
            else:
                print("Unknown target == 1 assign::: %s" % (ast.dump(node)))
                return
            get_pos(target)
            get_pos(node.value)
            sep_print()
        else:
             print("More than 1 target assign::: %s" % (ast.dump(node)))
             sep_print()
        # print(ast.dump(node))
        # print("", end='')

    # @recursive
    # def visit_BinOp(self, node):
    #     """ visit a BinOp node and visits it recursively"""
    #     print(type(node).__name__, type(node.left).__name__, type(node.right).__name__)
    #     print(ast.dump(node))
    #     pass

    @recursive
    def visit_Subscript(self, node):
        # print(ast.dump(node))
        # print("line: %s" % (node.lineno))
        # print("", end='')
        # sep_print()
        pass

    @recursive
    def visit_Index(self, node):
        # print(ast.dump(node))
        # print("line: %s" % (node.value.lineno))
        # print("", end='')
        # sep_print()
        pass

    @recursive
    def visit_Attribute(self, node):
        # print(type(node).__name__)
        # if isinstance(node.value, ast.Str):
        #     print(node.value.s)
        # print(ast.dump(node))
        # print("", end='')
        pass

    @recursive
    def visit_Str(self, node):
        # print(type(node).__name__)
        pass

    @recursive
    def visit_ListComp(self, node):
        pass

    @recursive
    def visit_List(self, node):
        pass

    @recursive
    def visit_DictComp(self, node):
        pass

    @recursive
    def visit_Dict(self, node):
        # print(type(node).__name__)
        # Looking for node
        # list => keys: <object>
        # list => values: <object>
        # print(ast.dump(node))
        # paired = zip(node.keys, node.values)
        # for blah in paired:
        #     print(blah)
        dict_kvp_printer(node)
        # print("", end='')

    @recursive
    def visit_SetComp(self, node):
        pass

    @recursive
    def visit_Set(self, node):
        pass

    @recursive
    def visit_Call(self, node):
        """ visit a Call node and visits it recursively"""
        # print(type(node).__name__)
        # Looking for node.keywords
        # keyword will be:
        # str => arg: <string>
        # ast.Str => value.s: <string>
        # print(ast.dump(node))
        # print("lineno: %s" % (node.lineno))
        # sep_print()
        # print("", end='')
        keyword_kvp_printer(node)

    @recursive
    def visit_Lambda(self, node):
        """ visit a Function node """
        print(type(node).__name__)

    @recursive
    def visit_Expr(self, node):
        pass

    @recursive
    def visit_BoolOp(self, node):
        print("", end='')
        pass

    @recursive
    def visit_Return(self, node):
        print("", end='')
        pass

    @recursive
    def visit_If(self, node):
        print("", end='')
        pass

    @recursive
    def visit_GeneratorExp(self, node):
        print("", end='')
        pass

    @recursive
    def visit_Compare(self, node):
        print("", end='')
        pass

    @recursive
    def visit_Try(self, node):
        print("", end='')
        pass

    @recursive
    def visit_Raise(self, node):
        print("", end='')
        pass

    @recursive
    def visit_Assert(self, node):
        print("", end='')
        pass

    @recursive
    def visit_AsyncFunctionDef(self, node):
        print("", end='')
        pass

    @recursive
    def visit_For(self, node):
        print("", end='')
        pass

    @recursive
    def visit_While(self, node):
        print("", end='')
        pass

    @recursive
    def visit_AsyncWith(self, node):
        print("", end='')
        pass

    @recursive
    def visit_FunctionDef(self, node):
        # """ visit a Function node and visits it recursively"""
        # print(type(node).__name__)
        # Looking for node.args
        # list => args: <ast.arg>
        # Looking for node.defaults
        # list => defaults: <object>
        # Will need to "line-up" the last element of the defaults list
        # with the last member of the args list to get the default values
        # print(ast.dump(node))
        # print(ast.dump(node))
        # print("lineno: %s" % (node.lineno))
        args = node.args.args
        defaults = node.args.defaults
        if not defaults:
            return
        num_args = len(args)
        num_defaults = len(defaults)
        remove = num_args - num_defaults
        trimmed_args = args[remove:]
        paired = zip(trimmed_args, defaults)
        for k, v in paired:
            if is_arg(k) and is_Str(v):
                print("func: '%s' => '%s'" % (k.arg, v.s))
                get_pos(k)
                get_pos(v)
                sep_print()

        # print(ast.dump(node))
        # print("", end='')

    @recursive
    def visit_ClassDef(self, node):
        pass

    @recursive
    def visit_Module(self, node):
        """ visit a Module node and the visits recursively"""
        pass

    def generic_visit(self, node):
        pass

    def custom_BinOp(self, node):
        if is_BinOp(node.left):
            # Only store the right node
            self.binop_stack.append(node.right)
            self.binop_stack.append(node.op)
            self.custom_BinOp(node.left)
        else:
            # At the end of the tree
            self.binop_stack.append(node.right)
            self.binop_stack.append(node.op)
            self.binop_stack.append(node.left)
            # print("I'm the last binop! list: %s" % (self.binop_stack))
            # Check if there is a single string in the stack
            found = False
            for n in self.binop_stack:
                if is_Str(n):
                    found = True
                    break
            if not found:
                print("No Str found in binop stack: %s" % (self.binop_stack))
                self.binop_stack = []
                return
            text_list = []
            for n in reversed(self.binop_stack):
                if is_Str(n):
                    value = "'%s'" % get_text(n)
                else:
                    value = get_text(n)
                text_list.append(value)
            # text_list = [get_text(n) for n in reversed(self.binop_stack)]
            self.binop_text = "%s" % ("".join(text_list))
            # print("BinOp text: '%s'" % ("".join(text_list)))
            # print("BinOp")
            self.binop_stack = []

class SimpleVisitor(ast.NodeVisitor):
    """ simple visitor for comparison """

    def recursive(func):
        """ decorator to make visitor work recursive """
        def wrapper(self, node):
            func(self,node)
            for child in ast.iter_child_nodes(node):
                self.visit(child)
        return wrapper

    def visit_Assign(self, node):
        """ visit a Assign node """
        # print(propnames(node))
        # print(dumpattrs(node))
        print(type(node).__name__)
        if isinstance(node.value, ast.Str):
            print(all_targets(node))
            print(node.value.s)

    def visit_BinOp(self, node):
        """ visit a BinOp node """
        print(type(node).__name__)

    def visit_Call(self, node):
        """ visit a Call node """
        print(type(node).__name__)

    def visit_Lambda(self, node):
        """ visit a Function node """
        print(type(node).__name__)

    def visit_FunctionDef(self, node):
        """ visit a Function node """
        print(type(node).__name__)

    @recursive
    def visit_Module(self, node):
        """ visit a Module node and the visits recursively, otherwise you
        wouldn't see anything here"""
        pass

    def generic_visit(self, node):
        pass

def main():
    import pprint
    # Sample 6 is python 2
    # filename = "./antlr/python/samples/sample6.py"
    filename = "./antlr/python/samples/sample3.py"
    with open(filename, "r") as source:
        data = source.read()
    tree = ast.parse(data)

    recursive_visitor = RecursiveVisitor()
    # simple_visitor = SimpleVisitor()
    tree = ast.parse(data)
    # print('\nvisit recursive\n')
    sep_print()
    recursive_visitor.visit(tree)
    # print(pprint.pformat(ast.dump(tree, include_attributes=True)))
    # print(ast.dump(tree, include_attributes=True))
    # print('\nvisit simple\n')
    # simple_visitor.visit(tree)

if __name__ == "__main__":
    main()
