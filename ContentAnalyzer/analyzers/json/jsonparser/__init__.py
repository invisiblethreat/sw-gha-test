"""jsonparser"""

import ply.lex as lex
import ply.yacc as yacc

from .lexer import *
from .parser import *

def parse(text: str):
    """Parse text.

    Args:

        text (str): Text to parse.

    Returns:

        List[Dict]: List of Dicts containing key/value pair positions.
    """

    create_document(text)

    ply_lexer = lex.lex()
    ply_parser = yacc.yacc()

    return ply_parser.parse(text, tracking=True, lexer=ply_lexer)
