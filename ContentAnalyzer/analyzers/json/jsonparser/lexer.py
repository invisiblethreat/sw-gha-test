"""Lexer"""

# pylint: disable=missing-docstring


class LexerError(Exception):
    """LexerError"""

# Token names
tokens = [
    'STRING',
    'NUMBER',
    'COMMA',
    'COLON',
    'TRUE',
    'FALSE',
    'NULL',
    'LBRACKET',
    'RBRACKET',
    'LSQBRACKET',
    'RSQBRACKET'
]


t_ignore = ' \t'
t_COMMA = r','
t_COLON = r':'
t_LBRACKET = r'\{'
t_RBRACKET = r'\}'
t_LSQBRACKET = r'\['
t_RSQBRACKET = r'\]'

def t_newline(t):
    r'\n+'

    t.lexer.lineno += len(t.value)

def t_STRING(t):
    r'"(([^"\\])|(\\["\\\/bfnrt])|(\\u[0-9a-f]{4}))*"'

    # Remove quotation marks
    t.value = t.value[1:-1]
    return t

def t_NUMBER(t):
    r'\-?(0|([1-9][0-9]*))(\.[0-9]*)?([eE][\+\-]?[0-9]*)?'

    try:
        t.value = int(t.value)
    except: # pylint: disable=bare-except
        t.value = float(t.value)
    return t

def t_TRUE(t):
    r'true'

    t.value = True
    return t

def t_FALSE(t):
    r'false'

    t.value = False
    return t

def t_NULL(t):
    r'null'

    t.value = None
    return t

def t_error(t): # pylint: disable=missing-docstring
    raise LexerError(t)
