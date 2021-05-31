"""Hcl2 parser"""

import os

from lark import Lark
from lark.tree import Tree

PARSER_CACHE_FILE = os.path.join(os.path.dirname(__file__), 'parser.cache')
LARK_FILE = os.path.join(os.path.dirname(__file__), 'hcl2.lark')

# pylint: disable=line-too-long
def create_parser_cache_file():
    """Create lark parser cache if it doesn't exist."""
    with open(LARK_FILE, 'r') as pf:
        Lark(pf.read(), parser="lalr", propagate_positions=True, cache=PARSER_CACHE_FILE)
# pylint: enable=line-too-long

if not os.path.exists(PARSER_CACHE_FILE):
    create_parser_cache_file()

with open(PARSER_CACHE_FILE, 'rb') as f:
    hcl2 = Lark.load(f) # type: ignore [attr-defined]

def parse(text: str) -> Tree:
    """Parse text to tree"""
    # Append new line as a workaround for https://github.com/lark-parser/lark/issues/237
    # Lark doesn't support a EOF token so our grammar can't look for "new line or end of file"
    # This means that all blocks must end in a new line even if the file ends
    # Append a new line as a temporary fix
    return hcl2.parse(text + "\n")
