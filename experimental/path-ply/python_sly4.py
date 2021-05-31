from sly import Lexer, Parser
from contexts import LEXER_DIRECTORY_CONTEXTS

class PathLexer(Lexer):
    tokens = { DIRECTORY_NAME, NAME }
    ignore = ' \t'
    literals = { '=', '+', '-', '*', '/', '(', ')' }

    # Tokens
    # DIRECTORY_NAME = r'[a-zA-Z0-9\-._@()# :~$+=áéğíıőöúüÜİ]+\/'
    # NAME = r'[a-zA-Z0-9\-._@()# :~$+=áéğíıőöúüÜİ]+'
    # SEPARATOR = r'\/'

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

class PathParser(Parser):
    tokens = PathLexer.tokens

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

if __name__ == '__main__':
    lexer = PathLexer()
    parser = PathParser()

    text = "usr/local/lib/R/site-library/BH/include/boost/math/distributions/triangular.hpp"

    for token in lexer.tokenize(text):
        print(token)

    print(parser.parse(lexer.tokenize(text)))
    print("breakpoint")
