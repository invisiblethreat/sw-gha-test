from sly import Lexer, Parser
from contexts import LEXER_DIRECTORY_CONTEXTS

class PathLexer(Lexer):
    tokens = { 
        DOT_CACHE_DIR,
        THIRD_PARTY_DIR,
        USR_SHARE_DOC,
        USR_LOCAL_LIB,
        PYSHARED_DIR,
        DEBPYTHON_DIR,
        DHPYTHON_DIR,
        GDB_DIR,
        USR_SHARE_PYTHON_BASE,
        USR_LIB_PYTHON_BASE_SITE_DIST_DIR,
        CONTEXT_NAME,
    }
    ignore = ' \t'
    literals = { '=', '+', '-', '*', '/', '(', ')' }

    # Tokens
    DOT_CACHE_DIR = r"dot_cache_dir"
    THIRD_PARTY_DIR = r"vendor_dir|thirdparty_dir"
    USR_SHARE_DOC = r"usr_dir share_dir doc_dir"
    USR_LOCAL_LIB = r"usr_dir local_dir lib_dir"
    PYSHARED_DIR = r"pyshared_dir"
    DEBPYTHON_DIR = r"debpython_dir"
    DHPYTHON_DIR = r"dhpython_dir"
    GDB_DIR = r"gdb_dir"
    USR_SHARE_PYTHON_BASE = r"usr_dir share_dir python_base_dir"
    USR_LIB_PYTHON_BASE_SITE_DIST_DIR = r"usr_dir lib_dir python_base_dir (site_packages_dir|dist_packages_dir)"

    CONTEXT_NAME = r"[a-zA-Z0-9\-._@()#:~$+=áéğíıőöúüÜİ]+"

    @_(r'\n+')
    def newline(self, t):
        self.lineno += t.value.count('\n')

    def error(self, t):
        print("Illegal character '%s'" % t.value[0])
        self.index += 1

# class PathParser(Parser):
#     tokens = PathLexer.tokens

#     def __init__(self):
#         self.names = { }
#         self.contexts = []

#     def add_context(self, name, ctx):
#         self.contexts.append((name, ctx))

#     def get_contexts(self):
#         return self.contexts.copy()

#     @_('parent_path NAME')
#     def full_path(self, p):
#         return p.parent_path + " "  + p.NAME

#     @_('DIRECTORY_NAME DIRECTORY_NAME')
#     def parent_path(self, p):
#         return p.DIRECTORY_NAME0 + " " + p.DIRECTORY_NAME1

#     @_('parent_path DIRECTORY_NAME')
#     def parent_path(self, p):
#         return p.parent_path + " " + p.DIRECTORY_NAME

#     @_('DIRECTORY_NAME')
#     def directory_name(self, p):
#         return p.DIRECTORY_NAME

#     @_('NAME')
#     def name(self, p):
#         return p.NAME

#     def error(self, p):
#         if p:
#             print("Syntax error at token", p.type)
#             # Just discard the token and tell the parser it's okay.
#             self.errok()
#         else:
#             print("Syntax error at EOF")

if __name__ == '__main__':
    lexer = PathLexer()
    # parser = PathParser()

    # text = "usr_dir share_dir file sourcecode_file source_code_python_file"
    # text = "usr_dir src_dir app_dir file sourcecode_file source_code_python_file"
    text = 'usr_dir local_dir lib_dir node_modules_dir node_module_package node_modules_dir node_module_package node_modules_dir node_module_package frontend_dir dist_dir file source_code_file source_code_javascript_file source_code_javascript_minified_file'

    for token in lexer.tokenize(text):
        print(token)

    # print(parser.parse(lexer.tokenize(text)))
    print("breakpoint")
