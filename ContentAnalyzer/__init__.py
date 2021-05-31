"""ContentAnalyzer"""

__version__ = "0.7.1"

__all__ = [
    'KeyValuePair',
    'LineColumnLocation',
    # 'get_analyzer',
    'get_analyzer_by_name',
    # 'get_analyzer_parameters',
    'get_lexer_by_name',
    'get_pygments_lexer_by_name',
    'get_analyzer_lexer_by_name',
]

import ContentAnalyzer.analyzers
import ContentAnalyzer.constants
import ContentAnalyzer.lexers
from ContentAnalyzer.base import (KeyValuePair, LineColumnLocation,
                                  get_analyzer_by_name,
                                  get_lexer_by_name, get_pygments_lexer_by_name,
                                  get_analyzer_lexer_by_name)
