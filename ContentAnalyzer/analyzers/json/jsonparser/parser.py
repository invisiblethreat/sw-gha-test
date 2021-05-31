"""Parser"""

# pylint: disable=global-statement

from typing import Dict
from collections import OrderedDict
from ply.lex import LexToken


class ParserError(Exception):
    """ParserError"""

def _make_token_position_dict(token: LexToken) -> Dict:
    """Make position dict for a token"""

    start_pos = token.lexpos + 1
    length = len(token.value)
    start_column = _find_column(token)

    position = {
        'start_pos': start_pos,
        'value': token.value,
        'end_pos': start_pos + length,
        'start_column': start_column,
        'end_column': start_column + length,
        'start_line': token.lineno,
        'end_line': token.lineno,
    }

    return position

def _make_kvp_position_dict(key_dict: Dict, value_dict: Dict) -> Dict:
    """Make kvp position dict"""

    position = {
        'key': key_dict['value'],
        'value': value_dict['value'],
        'start_pos': value_dict['start_pos'],
        'end_pos': value_dict['end_pos'],
        'start_line': value_dict['start_line'],
        'end_line': value_dict['end_line'],
        'start_column': value_dict['start_column'],
        'end_column': value_dict['end_column'],
    }
    return position

KVPS = list()
TEXT = None

def _find_column(token: LexToken) -> int:
    """Find the column for a token"""
    global TEXT
    line_start = TEXT.rfind('\n', 0, token.lexpos) + 1
    return (token.lexpos - line_start) + 1

def create_document(text: str):
    """Create new document and text"""

    global TEXT, KVPS
    KVPS = list()
    TEXT = text


def p_start(p):
    """start : array
             | object"""
    # p[0] = p[1]
    global KVPS
    p[0] = KVPS


def p_object(p):
    """object : LBRACKET members RBRACKET
              | LBRACKET RBRACKET"""
    p[0] = OrderedDict()
    if len(p) == 4:
        for item in p[2]:
            p[0][item[0]] = item[1]

def p_members(p):
    """members : pair
               | pair COMMA members"""
    p[0] = [p[1]]
    if len(p) == 4:
        for item in p[3]:
            p[0].append(item)

def p_pair(p):
    """pair : STRING COLON value"""
    global KVPS
    key = p[1]
    value = p[3].value

    if isinstance(key, str) and isinstance(value, str):
        key_dict = _make_token_position_dict(p.slice[1])
        # p3 will be a LexToken already so no need to slice
        value_dict = _make_token_position_dict(p[3])
        KVPS.append(_make_kvp_position_dict(key_dict, value_dict))

    p[0] = [p[1], p[3]]

def p_array(p):
    """array : LSQBRACKET RSQBRACKET
             | LSQBRACKET elements RSQBRACKET"""
    p[0] = []
    if len(p) == 4:
        for item in p[2]:
            p[0].append(item)

def p_elements(p):
    """elements : value
                | value COMMA elements"""
    p[0] = [p[1]]
    if len(p) == 4:
        for item in p[3]:
            p[0].append(item)

def p_value(p):
    """value : STRING
             | NUMBER
             | object
             | array
             | TRUE
             | FALSE
             | NULL"""
    p[0] = p.slice[1]

def p_error(p): # pylint: disable=missing-docstring
    raise ParserError(p)
