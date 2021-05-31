"""phpparser"""

from typing import List, Dict

from . import lexer
from .parser import make_parser
from . import ast


def parse(text: str) -> List[Dict]:
    """Parse text.

    Args:

        text (str): Text to parse.

    Returns:

        List[KeyValuePair]: List of KeyValuePair.
    """

    from ContentAnalyzer.analyzers.php.phpparser.visitor import PhpVisitor

    parser = make_parser()

    body_list = [ast for ast in parser.parse(text, lexer=lexer.lexer, tracking=True)]

    lineno = body_list[0].lineno
    lexpos = body_list[0].lexpos

    body = ast.Body(body_list, lineno=lineno, lexpos=lexpos) # type: ignore [operator]

    visitor = PhpVisitor(text=text)
    visitor.walk(body, None)

    matches = visitor.get_matches()

    parser.restart()
    lexer.reset()

    return matches
