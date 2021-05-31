import sys
from lark import Lark, Transformer

# content = """(.heh.babe)"""
content = """(.heh.babe)"""

dsl_grammar = r"""
    ?value: expression
          | full_accessor
          | accessor
          | evaluator
          | SIGNED_NUMBER      -> number
          | "true"             -> true
          | "false"            -> false
          | "null"             -> nulld

    expression : "(" value ")"

    full_accessor : accessor ( accessor )*

    accessor : field string

    field : "."

    evaluator: "contains"
             | "icontains"
             | "startswith"
             | "istartswith"
             | "endswith"
             | "iendswith"
             | "regexp"
             | "iregexp"
             | "in"

    string : /[a-z]+/

    %import common.SIGNED_NUMBER
    """

class TreeToJson(Transformer):
    def string(self, s):
        (s,) = s
        return s[:]
    # def accessor(self, s):
    #     # (s,) = s
    #     return str(s)
    # def full_accessor(self, s):
    #     return s
    def number(self, n):
        (n,) = n
        return float(n)

    list = list
    pair = tuple
    dict = dict

    # expression = lambda self, n: n
    evaluator = lambda self, n: n
    accessor = lambda self, n: n
    # full_accessor = lambda self, n: n
    field = lambda self, n: "."

    null = lambda self, _: None
    true = lambda self, _: True
    false = lambda self, _: False

parser = Lark(dsl_grammar, start='value', lexer='standard')

if __name__ == '__main__':
    # if len(sys.argv) > 1:
    #     filename = sys.argv[1]
    # else:
    #     filename = "generated.json"
    # with open(filename) as f:
    #     tree = parser.parse(f.read())
    tree = parser.parse(content)
    print(TreeToJson().transform(tree))
