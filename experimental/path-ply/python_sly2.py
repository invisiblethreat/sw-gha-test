from sly import Lexer, Parser
from contexts import LEXER_DIRECTORY_CONTEXTS

class CalcLexer(Lexer):
    # tokens = { DIRECTORY_NAME, NAME }
    tokens = { DIRECTORY_NAME, NAME }
    ignore = ' \t'
    literals = { '=', '+', '-', '*', '/', '(', ')' }

    # Tokens
    # DIRECTORY_NAME = r'[a-zA-Z0-9\-._@()# :~$+=áéğíıőöúüÜİ]+\/'
    # NAME = r'[a-zA-Z0-9\-._@()# :~$+=áéğíıőöúüÜİ]+'
    # SEPARATOR = r'\/'

    # @_(r'\d+')
    # def NUMBER(self, t):
    #     t.value = int(t.value)
    #     return t

    @_(r'[a-zA-Z0-9\-._@()# :~$+=áéğíıőöúüÜİ]+\/')
    def DIRECTORY_NAME(self, t):
        # t.value = t.value[0:-1]
        # t.type = LEXER_DIRECTORY_CONTEXTS.get(t.value, "GENERIC_DIR")
        return t

    @_(r'[a-zA-Z0-9\-._@()# :~$+=áéğíıőöúüÜİ]+')
    def NAME(self, t):
        # print("", end='')
        # t.type = "FILE"
        return t

    @_(r'\n+')
    def newline(self, t):
        self.lineno += t.value.count('\n')

    def error(self, t):
        print("Illegal character '%s'" % t.value[0])
        self.index += 1

class CalcParser(Parser):
    tokens = CalcLexer.tokens

    # precedence = (
    # #     ('left', '+', '-'),
    # #     ('left', '*', '/'),
    # #     ('right', 'UMINUS'),
    #     ('left', 'DIRECTORY_NAME'),
    #     ('right', 'NAME'),
    # )

    def __init__(self):
        self.names = { }
        self.contexts = []

    def add_context(self, name, ctx):
        self.contexts.append((name, ctx))

    def get_contexts(self):
        return self.contexts.copy()

    @_('parent_path NAME')
    def full_path(self, p):
        return p.parent_path + " "  + p.NAME

    @_('DIRECTORY_NAME DIRECTORY_NAME')
    def parent_path(self, p):
        return p.DIRECTORY_NAME0 + " " + p.DIRECTORY_NAME1

    @_('parent_path DIRECTORY_NAME')
    def parent_path(self, p):
        return p.parent_path + " " + p.DIRECTORY_NAME

    @_('DIRECTORY_NAME')
    def directory_name(self, p):
        return p.DIRECTORY_NAME

    # @_('parent_path NAME')
    # def full_path(self, p):
    #     # context_name = LEXER_DIRECTORY_CONTEXTS.get(p.DIRECTORY_NAME, 'GENERIC_DIR')
    #     # self.add_context(context_name, p)
    #     return p

    @_('NAME')
    def name(self, p):
        return p.NAME

    def error(self, p):
        if p:
            print("Syntax error at token", p.type)
            # Just discard the token and tell the parser it's okay.
            self.errok()
        else:
            print("Syntax error at EOF")

    # @_('expr "+" expr')
    # def expr(self, p):
    #     return p.expr0 + p.expr1

    # @_('expr "-" expr')
    # def expr(self, p):
    #     return p.expr0 - p.expr1

    # @_('expr "*" expr')
    # def expr(self, p):
    #     return p.expr0 * p.expr1

    # @_('expr "/" expr')
    # def expr(self, p):
    #     return p.expr0 / p.expr1

    # @_('"-" expr %prec UMINUS')
    # def expr(self, p):
    #     return -p.expr

    # @_('"(" expr ")"')
    # def expr(self, p):
    #     return p.expr

    # @_('NUMBER')
    # def expr(self, p):
    #     return p.NUMBER

    # @_('NAME')
    # def expr(self, p):
    #     try:
    #         return self.names[p.NAME]
    #     except LookupError:
    #         print("Undefined name '%s'" % p.NAME)
    #         return 0

class Path():

    def __init__(self):
        self.contexts = []

    def add_context(self, name, token):
        self.contexts.append((name, token))

    def get_contexts(self):
        return self.contexts.copy()

    def add_token(self, token):
        if token.type == "DIRECTORY_NAME":
            context_name = LEXER_DIRECTORY_CONTEXTS.get(token.value, 'GENERIC_DIR')
        elif token.type == "NAME":
            # context_name = LEXER_FILE_CONTEXTS.get(token.value, 'FILE')
            context_name = "FILE"
        self.add_context(context_name, token)


if __name__ == '__main__':
    lexer = CalcLexer()
    parser = CalcParser()
    # while True:
    #     try:
    #         text = input('calc > ')
    #     except EOFError:
    #         break
    #     if text:
    #         # parser.parse(lexer.tokenize(text))
    #         for token in lexer.tokenize(text):
    #             print(token)
    text = "usr/local/lib/R/site-library/BH/include/boost/math/distributions/triangular.hpp"
    # p = Path()
    for token in lexer.tokenize(text):
        # p.add_token(token)
        print(token)
    print(parser.parse(lexer.tokenize(text)))
    print("breakpoint")
