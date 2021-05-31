"""Main stuff"""

import importlib
from typing import Dict, Tuple, Union

import attr

IGNORE_KVP_VARIABLES = (
    'start_token',
    'parser_node',
    'line_positions',
    'esprima_node',
    'comment'
)

UNICODE_STRING_TRIPLE_SINGLE_QUOTE = "u'''"
UNICODE_STRING_TRIPLE_DOUBLE_QUOTE = 'u"""'
BYTE_STRING_TRIPLE_SINGLE_QUOTE = "b'''"
BYTE_STRING_TRIPLE_DOUBLE_QUOTE = 'b"""'
STRING_TRIPLE_SINGLE_QUOTE = "'''"
STRING_TRIPLE_DOUBLE_QUOTE = '"""'

UNICODE_STRING_SINGLE_QUOTE = "u'"
UNICODE_STRING_DOUBLE_QUOTE = 'u"'
BYTE_STRING_SINGLE_QUOTE = "b'"
BYTE_STRING_DOUBLE_QUOTE = 'b"'
STRING_SINGLE_QUOTE = "'"
STRING_DOUBLE_QUOTE = '"'

FORMATTED_TRIPLE_QUOTE_STRINGS = (
    UNICODE_STRING_TRIPLE_SINGLE_QUOTE,
    UNICODE_STRING_TRIPLE_DOUBLE_QUOTE,
    BYTE_STRING_TRIPLE_SINGLE_QUOTE,
    BYTE_STRING_TRIPLE_DOUBLE_QUOTE,
)

BARE_TRIPLE_QUOTE_STRINGS = (
    STRING_TRIPLE_SINGLE_QUOTE,
    STRING_TRIPLE_DOUBLE_QUOTE
)

ALL_TRIPLE_QUOTE_STRINGS = (
    UNICODE_STRING_TRIPLE_SINGLE_QUOTE,
    UNICODE_STRING_TRIPLE_DOUBLE_QUOTE,
    BYTE_STRING_TRIPLE_SINGLE_QUOTE,
    BYTE_STRING_TRIPLE_DOUBLE_QUOTE,
    STRING_TRIPLE_SINGLE_QUOTE,
    STRING_TRIPLE_DOUBLE_QUOTE
)

FORMATTED_QUOTE_STRINGS = (
    UNICODE_STRING_SINGLE_QUOTE,
    UNICODE_STRING_DOUBLE_QUOTE,
    BYTE_STRING_SINGLE_QUOTE,
    BYTE_STRING_DOUBLE_QUOTE,
)

BARE_QUOTE_STRINGS = (
    STRING_SINGLE_QUOTE,
    STRING_DOUBLE_QUOTE
)

ALL_QUOTE_STRINGS = (
    UNICODE_STRING_SINGLE_QUOTE,
    UNICODE_STRING_DOUBLE_QUOTE,
    BYTE_STRING_SINGLE_QUOTE,
    BYTE_STRING_DOUBLE_QUOTE,
    STRING_SINGLE_QUOTE,
    STRING_DOUBLE_QUOTE
)

def get_analyzer_by_name(name):
    """Get analyzer by name."""

    blah = getattr(importlib.import_module("ContentAnalyzer.analyzers"), name)

    return blah


# pylint: disable=broad-except
def get_lexer_by_name(name):
    """Get a pygments or ContentAnalyzer lexer by name."""

    try:
        return get_pygments_lexer_by_name(name)
    except Exception:
        # Try ContentAnalyzer now
        return get_analyzer_lexer_by_name(name)
# pylint: enable=broad-except


def get_analyzer_lexer_by_name(name):
    """Get a ContentAnalyzer lexer by name."""

    blah = getattr(importlib.import_module("ContentAnalyzer.lexers"), name)

    return blah()


def get_pygments_lexer_by_name(name):
    """Get a pygments lexer by name."""

    from pygments.lexers import get_lexer_by_name as pygments_get_lexer_by_name

    blah = pygments_get_lexer_by_name(name)

    return blah


def _strip_whitespace(text: str) -> Tuple[str, int, int, int]:
    """Strip any leading/ending whitespace.

    Args:

        text (str): Text to strip whitespace from.

    Returns:

        Tuple[str, int, int, int]: Tuple containing new string, length,
            start trim position, and end trim position.
    """
    left_pad = 0
    right_pad = 0

    length_text = len(text)

    # Calculate left strip
    left_stripped_code = text.lstrip()
    length_left_stripped_code = len(left_stripped_code)

    if length_left_stripped_code != length_text:
        left_pad = length_text - length_left_stripped_code

    # Calculate right strip
    right_stripped_code = left_stripped_code.rstrip()
    length_right_stripped_code = len(right_stripped_code)

    if length_right_stripped_code != length_left_stripped_code:
        right_pad = length_left_stripped_code - length_right_stripped_code

    # Return right stripped and pad values
    return right_stripped_code, length_right_stripped_code, left_pad, right_pad


# pylint: disable=line-too-long
def _strip_quotes(text: str) -> Tuple[str, int, int, int]:
    """Strip any leading/ending quotes if wrapped in the same quote type.

    Also remove python unicode/bytes strings.

    Args:

        text (str): Text to strip quotes from.

    Returns:

        Tuple[str, int, int, int]: Tuple containing new string, length,
            start trim position, and end trim position.
    """

    start_trim = 0
    end_trim = 0

    if text.startswith(FORMATTED_TRIPLE_QUOTE_STRINGS) and text.endswith(BARE_TRIPLE_QUOTE_STRINGS):
        start_trim = 4
        end_trim = 3
    elif text.startswith(BARE_TRIPLE_QUOTE_STRINGS) and text.endswith(BARE_TRIPLE_QUOTE_STRINGS):
        start_trim = 3
        end_trim = 3
    elif text.startswith(FORMATTED_QUOTE_STRINGS) and text.endswith(BARE_QUOTE_STRINGS):
        start_trim = 2
        end_trim = 1
    elif text.startswith(STRING_DOUBLE_QUOTE) and text.endswith(STRING_DOUBLE_QUOTE):
        start_trim = 1
        end_trim = 1
    elif text.startswith(STRING_SINGLE_QUOTE) and text.endswith(STRING_SINGLE_QUOTE):
        start_trim = 1
        end_trim = 1
    else:
        return text, len(text), start_trim, end_trim

    new_text = text[start_trim:-end_trim]
    length = len(new_text)

    return new_text, length, start_trim, end_trim
# pylint: enable=line-too-long


@attr.s(kw_only=True, slots=True)
class LineColumnLocation:
    """LineColumnLocation."""

    start_token = attr.ib(default=None)
    pos_calculate = attr.ib(default=None)

    comment: bool = attr.ib(default=False)

    def __getstate__(self) -> dict:
        # Custom __getstate__ to remove undesired class variables
        # class serialization to dict/pickle
        temp_dict = {k: v for k, v in self.__dict__.items() if k not in IGNORE_KVP_VARIABLES}
        return temp_dict

    text: str = attr.ib(default=None)
    start_line: int = attr.ib(default=None)
    start_column: int = attr.ib(default=None)
    start_pos: int = attr.ib(default=None)
    end_line: int = attr.ib(default=None)
    end_column: int = attr.ib(default=None)
    end_pos: int = attr.ib(default=None)
    length: int = attr.ib(default=None)


    def __attrs_post_init__(self):
        if self.start_token is not None:
            # This seems to be used by the PhpAnalyzer using ANTLR4
            self.set_attributes_from_token()


    def set_attributes_from_token(self) -> None:
        """Set attributes from a token"""

        # TODO: May also need to handle the stop token too?

        self.text = str(self.start_token.text)
        self.start_pos = self.start_token.start
        # Needs to be +1 otherwise last char gets cut off
        self.end_pos = self.start_token.stop + 1
        # self.line = LineColumnLocation(token=self.token)
        self.start_line = self.start_token.line
        self.start_column = self.start_token.column

    # pylint: disable=line-too-long
    def from_node(self, node: Union['parso.Node', 'esprima.Node', 'javalang.Node'], comment: bool = False) -> None:
        """Set from a parser's node.

        Args:

            node (Union['parso.Node', 'esprima.Node', 'javalang.Node']): Parso, esprima, or javalang node.
            comment (bool, optional): Token is a comment. Defaults to False.

        Returns:

            None.
        """

        node_function_mapping = {
            'parso.python.tree': calculate_position_from_parso_node,
            'esprima.nodes': calculate_position_from_esprima_node,
            'javalang.tree': calculate_position_from_javalang_node,
        }

        module_name = node.__class__.__module__
        if module_name not in node_function_mapping:
            raise TypeError(f"Don't know how to process node {node}")

        func = node_function_mapping[module_name]

        if comment:
            self.comment = True

        position_dict = func(node, self.pos_calculate, comment=comment)
        self.text = position_dict['text']
        del position_dict['text']
        self.set_position_from_dict(position_dict)
    # pylint: disable=line-too-long

    # pylint: disable=line-too-long
    def from_parso_node(self, node: 'parso.Node', comment: bool = False) -> None:
        """Set from Parso node.

        Args:

            node (parso.Node): Parso node.
            comment (bool, optional): Token is a comment. Defaults to False.

        Returns:

            None.
        """

        if comment:
            self.comment = True

        position_dict = calculate_position_from_parso_node(node, self.pos_calculate, comment=comment)
        self.text = position_dict['text']
        del position_dict['text']
        self.set_position_from_dict(position_dict)
    # pylint: disable=line-too-long

    # pylint: disable=line-too-long
    def set_position_from_dict(self, position_dict: Dict) -> None:
        """Set position from dictionary.

        Args:

            position_dict (Dict): Dictionary of position information.

        Returns:

            None.
        """
        for k, v in position_dict.items():
            setattr(self, k, v)

        # for k in ('start_pos', 'end_pos', 'start_line', 'start_column', 'end_line', 'end_column', 'length'):
        #     setattr(self, k, position_dict[k])
    # pylint: enable=line-too-long


@attr.s(kw_only=True, slots=True)
class NewKeyValuePair:
    """NewKeyValuePair.

    To replace both of the other KeyValuePair classes.
    """

    key: str = attr.ib()
    value: str = attr.ib()
    start_pos: int = attr.ib()
    end_pos: int = attr.ib()
    start_line: int = attr.ib()
    end_line: int = attr.ib()
    start_column: int = attr.ib()
    end_column: int = attr.ib()

    def to_dict(self) -> Dict:
        """Serialize class to dict"""

        return attr.asdict(self)


# TODO: See if this class or the one in lexers can be axed.
@attr.s(kw_only=True, slots=True, frozen=True)
class KeyValuePair:
    """KeyValuePair.

    BEWARE! There is a near duplicate of this class in ContentAnalyzer.lexers.base!
    """

    key: 'Node' = attr.ib()
    value: 'Node' = attr.ib()

    def get_key(self) -> str:
        """Get key's value"""
        return self._get_location_property(self.key, 'text')

    def get_value(self) -> str:
        """Get value's value"""
        return self._get_location_property(self.value, 'text')

    def get_key_start_pos(self) -> int:
        """Get key start_pos"""
        return self._get_location_property(self.key, 'start_pos')

    def get_key_start_line(self) -> int:
        """Get key start_line"""
        return self._get_location_property(self.key, 'start_line')

    def get_key_start_column(self) -> int:
        """Get key start_column"""
        return self._get_location_property(self.key, 'start_column')

    def get_key_end_pos(self) -> int:
        """Get key end_pos"""
        return self._get_location_property(self.key, 'end_pos')

    def get_key_end_line(self) -> int:
        """Get key end_line"""
        return self._get_location_property(self.key, 'end_line')

    def get_key_end_column(self) -> int:
        """Get key end_column"""
        return self._get_location_property(self.key, 'end_column')

    def get_value_start_pos(self) -> int:
        """Get value start_pos"""
        return self._get_location_property(self.value, 'start_pos')

    def get_value_start_line(self) -> int:
        """Get value start_line"""
        return self._get_location_property(self.value, 'start_line')

    def get_value_start_column(self) -> int:
        """Get value start_column"""
        return self._get_location_property(self.value, 'start_column')

    def get_value_end_pos(self) -> int:
        """Get value end_pos"""
        return self._get_location_property(self.value, 'end_pos')

    def get_value_end_line(self) -> int:
        """Get value end_line"""
        return self._get_location_property(self.value, 'end_line')

    def get_value_end_column(self) -> int:
        """Get value end_column"""
        return self._get_location_property(self.value, 'end_column')

    def _get_location(self, where):
        """If where has 'get_location' attribute, return it"""
        if hasattr(where, 'get_location'):
            return where.get_location()

    def _get_location_property(self, where, name, default_value=0):
        """Get 'name' attribute from 'where' if it exists, otherwise try get_location"""

        if hasattr(where, name):
            return getattr(where, name)

        location = self._get_location(where)
        if location is None:
            return default_value

        if hasattr(location, name):
            return getattr(location, name)

        return default_value

    def get_key_location(self):
        """Get key's location"""
        return self._get_location(self.key)

    def get_value_location(self):
        """Get value's location"""
        return self._get_location(self.key)

    def get_leak_kwargs(self) -> dict:
        """Get a dict suitable to instantiate a Leak as kwargs"""
        return self.to_dict()

    def get_leak_position_kwargs(self) -> dict:
        """Temporary"""
        return self.to_dict()

    def to_dict(self) -> dict:
        """Serialize class to dict"""

        value = {
            'key': self.get_key(),
            'value': self.get_value(),
            'start_pos': self.get_value_start_pos(),
            'end_pos': self.get_value_end_pos(),
            'start_line': self.get_value_start_line(),
            'end_line': self.get_value_end_line(),
            'start_column': self.get_value_start_column(),
            'end_column': self.get_value_end_column(),
        }

        return value


@attr.s(kw_only=True, slots=True)
class PosCalculate:
    """PosCalculate.

    Args:

        text (str): Text to calculate positions for.
    """

    text: str = attr.ib()
    lengths = attr.ib(factory=dict)
    start_offsets = attr.ib(factory=dict)

    def __attrs_post_init__(self):

        # Calculate only start_offsets when instantiating
        self.start_offsets = {0: 0}
        current_offset = 0
        for i, n in enumerate(self.text.split('\n')): # pylint: disable=no-member
            # Include one for the missing new line
            line_length = len(n) + 1
            self.lengths[i] = line_length
            self.start_offsets[i + 1] = current_offset + line_length
            current_offset += line_length


    def get_pos(self, line_number: int, column: int = 0) -> int:
        """Get an absolute position for a line number and optional column number.

        Args:

            line_number (int): Line number to get absolute position for.
            column (int, optional): Column number to use to calculate position. Defaults to 0.

        Returns:

            int: Absolute position/offset of line/column in file.
        """
        # start_offsets starts at 0 so line_number 1 is at index 0
        offset = self.start_offsets[line_number - 1] + column
        return offset


    def get_end_pos(self, text: str, start_pos: int) -> int:
        """Get an absolute ending position for a string given a start position.

        Args:

            text (str): Text to calculate end position for.
            start_pos (int): Starting position of text.

        Returns:

            int: Absolute end position/offset of text at start_pos position.
        """
        return start_pos + len(text) - 1


    def get_line_and_column(self, pos: int) -> Tuple[int, int]:
        """Get line and column number from an absolute position.

        Args:

            pos (int): Absolute position/offset in file.

        Returns:

            Tuple[int, int]: Line and column number of pos in file.
        """
        line = 0
        column = 0
        for line_number, start_offset in self.start_offsets.items():
            if pos <= start_offset:
                # Actual line number is fine
                # and the offset to use is - 1
                line = line_number
                offset = self.start_offsets[line_number - 1]
                column = pos - offset
                break

        return line, column


    # pylint: disable=line-too-long
    def get_position_dict(self, text: str, start_pos: int = None, line_number: int = None, column: int = 0) -> int:
        """Get a position dict given a string and a starting position.

        Must provide either start_pos or line_number to get position. Column is optional.

        Args:

            text (str): Text to get position for.
            start_pos (int, optional): Absolute position/offset of text in file. Defaults to None.
            line_number (int, optional): Starting line number of text in file. Defaults to None.
            column (int, optional): Starting column of text in file. Defaults to 0.

        Raises:
            ValueError: If not start_pos or line_number is provided.

        Returns:

            Dict: Dictionary containing start_pos, end_pos, start_line, end_line, start_column, end_column, length of text in file.
        """
        if start_pos is not None:
            # Use start pos
            # Subtract 1 here to account for array indexes starting at 0
            # So if 'production' is at start_pos 1426 (the absolute offset of 'p')
            # and its length is 10 then its end_pos should 1435, not 1436!
            end_pos = start_pos + len(text) - 1
            start_line, start_column = self.get_line_and_column(start_pos)
            end_line, end_column = self.get_line_and_column(end_pos)
        elif line_number is not None:
            start_pos = self.get_pos(line_number, column)
            # Subtract 1 here to account for array indexes starting at 0
            # So if 'production' is at start_pos 1426 (the absolute offset of 'p')
            # and its length is 10 then its end_pos should 1435, not 1436!
            end_pos = start_pos + len(text) - 1
            start_line = line_number
            start_column = column
            end_line, end_column = self.get_line_and_column(end_pos)
        else:
            raise ValueError("Must provide values for start_pos or line_number!")

        position_dict = {
            'start_pos': start_pos,
            'end_pos': end_pos,
            'start_line': start_line,
            'start_column': start_column,
            'end_line': end_line,
            'end_column': end_column,
            'length': end_pos - start_pos,
        }

        return position_dict
    # pylint: enable=line-too-long


# pylint: disable=line-too-long
def calculate_position_from_parso_node(node: 'parso.Node', pos_calculate: PosCalculate, comment: bool = False) -> Dict[str, int]:
    """Calculate position of text from a parso.Node.

    Args:

        node (parso.Node): Parso node.
        pos_calculate (PosCalculate): PosCalculate instance.
        comment (bool, optional): Whether or not node represents a comment. Defaults to False.

    Returns:

        Dict[str, int]: Dict containing position name and offset information.
    """

    end_trim = 0
    end_column = 0

    if comment:
        # TODO: Fix start/end position by adjusting for leading/trailing whitespace
        # Ending position can also be calculated by adding the number of newlines
        # in comment to the starting line number
        start_line, start_column = node.get_start_pos_of_prefix()

        if hasattr(node, 'prefix'):
            text = node.prefix
        else:
            raise AttributeError("Comment node has no prefix attribute!")

    else:
        start_line, start_column = node.start_pos

        if hasattr(node, 'value'):
            text = node.value
        else:
            code = node.get_code()
            text, _, left_pad, _ = _strip_whitespace(code)
            start_column += left_pad

        text, _, start_trim, _ = _strip_quotes(text)
        # text, _, start_trim, end_trim = _strip_quotes(text)
        start_column += start_trim

    position_dict = pos_calculate.get_position_dict(text, line_number=start_line, column=start_column)
    # Add 1 back to the end_pos here due to parso string node values being encapsulated in quotes.
    # position_dict['end_pos'] += 1
    # position_dict['end_column'] += 1
    position_dict['text'] = text
    return position_dict
# pylint: enable=line-too-long

# pylint: disable=line-too-long
def calculate_position_from_javalang_node(node: 'javalang.Node', pos_calculate: PosCalculate, comment: bool = False) -> Dict[str, int]:
    """Calculate position of text from a javalang.Node.

    Args:

        node (javalang.Node): javalang node.
        pos_calculate (PosCalculate): PosCalculate instance.
        comment (bool, optional): Whether or not node represents a comment. Defaults to False.

    Returns:

        Dict[str, int]: Dict containing position name and offset information.
    """
    kind = node.__class__.__name__

    if kind == "VariableDeclarator":
        text = node.name
        if hasattr(node.initializer, 'position') and node.initializer.position is not None:
            position = node.initializer.position
        elif node.position is not None:
            position = node.position
        else:
            raise RuntimeError(f"Can't determine node's position! Node: {node}")
    elif kind == "Literal":
        text = node.value
        position = node.position
    elif kind == "MethodInvocation":
        text = node.member
        position = node.position
    else:
        raise ValueError(f"Don't know how to handle node kind: {kind}")

    start_line = position.line
    start_column = position.column

    code = text
    text, _, left_pad, _ = _strip_whitespace(code)
    start_column += left_pad

    text, _, start_trim, _ = _strip_quotes(text)
    start_column += start_trim

    # To adjust for something?
    start_column -= 1

    position_dict = pos_calculate.get_position_dict(text, line_number=start_line, column=start_column)
    position_dict['text'] = text
    return position_dict
# pylint: disable=line-too-long

# pylint: disable=line-too-long
def calculate_position_from_esprima_node(node: 'esprima.Node', pos_calculate: PosCalculate, comment: bool = False) -> Dict[str, int]:
    """Calculate position of text from a esprima.Node.

    Args:

        node (esprima.Node): esprima node.
        pos_calculate (PosCalculate): PosCalculate instance.
        comment (bool, optional): Whether or not node represents a comment. Defaults to False.

    Returns:

        Dict[str, int]: Dict containing position name and offset information.
    """

    start_line = node.loc.start.line
    # Add one to column for some reason?
    start_column = node.loc.start.column + 1

    # TODO: Fix/add MemberExpression node
    if hasattr(node, 'name') and getattr(node, 'name') is not None:
        text = node.name
    elif hasattr(node, 'value') and getattr(node, 'value') is not None:
        text = str(node.value)
    elif hasattr(node, 'operator') and getattr(node, 'operator') is not None:
        text = node.operator
    else:
        raise AttributeError(f"Can't find name or value attribute on node '{node}'")

    position_dict = pos_calculate.get_position_dict(text, line_number=start_line, column=start_column)
    position_dict['text'] = text
    position_dict['end_line'] = node.loc.end.line
    # position_dict['end_column'] = node.loc.end.column
    return position_dict
# pylint: enable=line-too-long
