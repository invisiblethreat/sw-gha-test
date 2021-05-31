"""Extract comments from code"""

import io
import re
import tokenize
from typing import Dict, List, Tuple
from enum import Enum

import attr


class Error(Exception):
    """Base Error class for all comment parsers."""


class FileError(Error):
    """Raised if there is an issue reading a given file."""


class UnterminatedCommentError(Error):
    """Raised if an Unterminated multi-line comment is encountered."""


@attr.s(kw_only=False, slots=True)
class Comment:
    """Comment.

    Args:

        text (str): Text of comment.
    """

    text = attr.ib()
    start_line: int = attr.ib(default=0)
    start_column: int = attr.ib(default=0)
    end_line: int = attr.ib(default=0)
    end_column: int = attr.ib(default=0)
    start_pos: int = attr.ib(default=0)
    end_pos: int = attr.ib(default=0)
    multiline: bool = attr.ib(default=False)
    length: int = attr.ib(default=0)

    def __attrs_post_init__(self):

        if self.end_pos == 0:
            self.end_pos = self.start_pos + len(self.text) - 1


    def to_dict(self, exclude: List[str] = None) -> Dict:
        """Serialize class to dict.

        Args:

            exclude (List[str], optional): A list of attributes to exclude. Defaults to None.

        Returns:

            Dict: Class serialized to a dictionary.
        """

        exclude = exclude or list()
        dikt = attr.asdict(self, filter=lambda attr, value: attr.name not in exclude)
        return dikt


@attr.s(kw_only=True, slots=True)
class PosCalculate:
    """PosCalculate.

    Args:

        text (str): Text to calculate positions for.
    """

    text = attr.ib()
    lengths = attr.ib(factory=dict)
    start_offsets = attr.ib(factory=dict)

    def __attrs_post_init__(self):

        self.start_offsets = {0: 0}
        current_offset = 0
        for i, n in enumerate(self.text.split('\n')):
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
        return start_pos + len(text)


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
            if pos < start_offset:
                # Actual line number is fine
                # and the offset to use is - 1
                line = line_number
                offset = self.start_offsets[line_number - 1]
                column = pos - offset
                break

        return line, column


    # pylint: disable=line-too-long
    def get_position_dict(self, text: str, start_pos: int = None, line_number: int = None, column: int = 0) -> Dict:
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
            end_pos = start_pos + len(text)
            start_line, start_column = self.get_line_and_column(start_pos)
            end_line, end_column = self.get_line_and_column(end_pos)
        elif line_number is not None:
            start_pos = self.get_pos(line_number, column)
            end_pos = start_pos + len(text)
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
def extract_python_comments(text: str) -> List[Comment]:
    """Extract comments from Python.

    Comments are identified using the tokenize module. Does not include function,
    class, or module docstrings. All comments are single line comments.

    Args:

        text (str): Code as a string.

    Raises:
        UnterminatedCommentError: Unterminated multi-line comment.

    Returns:

        List[Comment]: List of Comment instances containing comments.
    """

    pos = PosCalculate(text=text)

    comments = []
    tokens = tokenize.tokenize(io.BytesIO(text.encode()).readline)
    for toknum, tokstring, tokloc, _, _ in tokens:
        if toknum is tokenize.COMMENT:
            # Removes leading '#' character.
            tokstring = tokstring[1:]
            line_number, column = tokloc
            position = pos.get_position_dict(tokstring, line_number=line_number, column=column)
            comments.append(Comment(tokstring, **position))
    return comments
# pylint: enable=line-too-long


def extract_javascript_comments(text: str) -> List[Comment]:
    """Extract comments from Javascript.

    Single-line comments begin with '//' and continue to the end of line.
    Multi-line comments begin with '/*' and end with '*/' and can span
    multiple lines of code. If a multi-line comment does not terminate
    before EOF is reached, then an exception is raised.
    Quoted strings are taken into account.

    Args:

        text (str): Code as a string.

    Raises:
        UnterminatedCommentError: Unterminated multi-line comment.

    Returns:

        List[Comment]: List of Comment instances containing comments.
    """
    pos = PosCalculate(text=text)
    state = 0
    current_comment = ''
    comments = []
    line_counter = 1
    comment_start_pos = 0
    string_char = ''
    for i, char in enumerate(text):
        if state == 0:
            # Waiting for comment start character or beginning of
            # string.
            if char == '/':
                state = 1
            elif char in ('"', "'"):
                string_char = char
                state = 5
        elif state == 1:
            # Found comment start character, classify next character and
            # determine if single or multi-line comment.
            if char == '/':
                state = 2
                comment_start_pos = i
            elif char == '*':
                comment_start_pos = i
                state = 3
            else:
                state = 0
        elif state == 2:
            # In single-line comment, read characters until EOL.
            if char == '\n':
                position = pos.get_position_dict(current_comment, comment_start_pos)
                comment = Comment(current_comment, **position)
                comments.append(comment)
                current_comment = ''
                comment_start_pos = None
                state = 0
            else:
                current_comment += char
        elif state == 3:
            # In multi-line comment, add characters until '*' is
            # encountered.
            if char == '*':
                state = 4
            else:
                current_comment += char
        elif state == 4:
            # In multi-line comment with asterisk found. Determine if
            # comment is ending.
            if char == '/':
                position = pos.get_position_dict(current_comment, comment_start_pos)
                comment = Comment(current_comment, multiline=True, **position)
                comments.append(comment)
                current_comment = ''
                comment_start_pos = None
                state = 0
            else:
                current_comment += '*'
                # Care for multiple '*' in a row
                if char != '*':
                    current_comment += char
                    state = 3
        elif state == 5:
            # In string literal, expect literal end or escape character.
            if char == string_char:
                state = 0
            elif char == '\\':
                state = 6
        elif state == 6:
            # In string literal, escaping current char.
            state = 5
            if char == '\n':
                line_counter += 1

    # EOF.
    if state in (3, 4):
        raise UnterminatedCommentError()
    if state == 2:
        # Was in single-line comment. Create comment.
        position = pos.get_position_dict(current_comment, comment_start_pos)
        comment = Comment(current_comment, **position)
        comments.append(comment)
    return comments


def extract_ruby_comments(text: str) -> List[Comment]:
    """Extract comments from Ruby.

    Comments start with a '#' character and run to the end of the line,
    http://ruby-doc.com/docs/ProgrammingRuby.

    Args:

        text (str): Code as a string.

    Raises:
        UnterminatedCommentError: Unterminated multi-line comment.

    Returns:

        List[Comment]: List of Comment instances containing comments.
    """

    pos = PosCalculate(text=text)
    pattern = r"""
        (?P<literal> ([\"'])((?:\\\2|(?:(?!\2)).)*)(\2)) |
        (?P<single> \#(?P<single_content>.*?)$)
    """
    compiled = re.compile(pattern, re.VERBOSE | re.MULTILINE)

    lines_indexes = []
    for match in re.finditer(r"$", text, re.M):
        lines_indexes.append(match.start())

    comments = []
    for match in compiled.finditer(text):
        kind = match.lastgroup

        if kind == "single":
            comment_content = match.group("single_content")
            comment_start_pos = match.start("single_content")
            position = pos.get_position_dict(comment_content, comment_start_pos)
            comment = Comment(comment_content, **position)
            comments.append(comment)

    return comments

class ShellState(Enum):
    """ShellState"""

    # BEGIN_WAITING_FOR_COMMENT_START_CHARACTER = 1
    WAITING_FOR_START = 1
    # READING_COMMENT_UNTIL_EOL = 2
    READING_UNTIL_EOL = 2
    # BEGIN_STRING_LITERAL_WAITING_END_OR_ESCAPE = 3
    WAITING_END_OR_ESCAPE = 3
    ESCAPING_CURRENT_CHARACTER_STRING_LITERAL = 4
    ESCAPING_CURRENT_CHARACTER_COMMENT = 5

def extract_shell_comments(text: str) -> List[Comment]:
    """Extract comments from Shell script.

    Comments start with an unquoted or unescaped '#' and continue on until the
    end of the line. A quoted '#' is one that is located within a pair of
    matching single or double quote marks. An escaped '#' is one that is
    immediately preceeded by a backslash '\'.

    Args:

        text (str): Code as a string.

    Raises:
        UnterminatedCommentError: Unterminated multi-line comment.

    Returns:

        List[Comment]: List of Comment instances containing comments.
    """

    pos = PosCalculate(text=text)
    # state = 0
    state = ShellState.WAITING_FOR_START
    string_char = ''
    current_comment = ''
    comments = []
    line_counter = 1
    comment_start_pos = None
    for i, char in enumerate(text):
        if state == ShellState.WAITING_FOR_START:
            # Waiting for comment start character, beginning of string,
            # or escape character.
            if char == '#':
                state = ShellState.READING_UNTIL_EOL
            elif char in ('"', "'"):
                string_char = char
                state = ShellState.WAITING_END_OR_ESCAPE
            elif char == '\\':
                state = ShellState.ESCAPING_CURRENT_CHARACTER_COMMENT
        elif state == ShellState.READING_UNTIL_EOL:
            # Found comment start character. Read comment until EOL.
            if char == '\n':
                # If the comment is empty then reset state and carry on
                if current_comment == '':
                    state = ShellState.WAITING_FOR_START
                else:
                    position = pos.get_position_dict(current_comment, comment_start_pos)
                    comment = Comment(current_comment, **position)
                    comments.append(comment)
                    current_comment = ''
                    comment_start_pos = None
                    state = ShellState.WAITING_FOR_START
            else:
                if comment_start_pos is None:
                    comment_start_pos = i
                current_comment += char
        elif state == ShellState.WAITING_END_OR_ESCAPE:
            # In string literal, wait for string end or escape char.
            if char == string_char:
                state = ShellState.WAITING_FOR_START
            elif char == '\\':
                state = ShellState.ESCAPING_CURRENT_CHARACTER_STRING_LITERAL
        elif state == ShellState.ESCAPING_CURRENT_CHARACTER_STRING_LITERAL:
            # Escaping current char, inside of string.
            state = ShellState.WAITING_END_OR_ESCAPE
        elif state == ShellState.ESCAPING_CURRENT_CHARACTER_COMMENT:
            # Escaping current char, outside of string.
            state = ShellState.WAITING_FOR_START
        if char == '\n':
            line_counter += 1

    # EOF.
    if state == ShellState.READING_UNTIL_EOL:
        # Was in single line comment. Create comment.
        position = pos.get_position_dict(current_comment, comment_start_pos)
        comment = Comment(current_comment, **position)
        comments.append(comment)
    return comments


# pylint: disable=line-too-long
def extract_go_comments(text: str) -> List[Comment]:
    """Extract comments from GO.

    Single-line comments begin with '//' and continue to the end of line.
    Multi-line comments begin with '/*' and end with '*/' and can span
    multiple lines of code. If a multi-line comment does not terminate
    before EOF is reached, then an exception is raised.

    Go comments are not allowed to start in a string or rune literal. This
    module makes sure to watch out for those.
    https://golang.org/ref/spec#Comments

    Args:

        text (str): Code as a string.

    Raises:
        UnterminatedCommentError: Unterminated multi-line comment.

    Returns:

        List[Comment]: List of Comment instances containing comments.
    """

    pos = PosCalculate(text=text)
    state = 0
    current_comment = ''
    comments = []
    line_counter = 1
    comment_start_pos = None
    string_char = ''
    for i, char in enumerate(text):
        if state == 0:
            # Waiting for comment start character or beginning of
            # string or rune literal.
            if char == '/':
                state = 1
            elif char in ('"', "'", '`'):
                string_char = char
                state = 5
        elif state == 1:
            # Found comment start character, classify next character and
            # determine if single or multi-line comment.
            if char == '/':
                state = 2
            elif char == '*':
                comment_start_pos = i
                state = 3
            else:
                state = 0
        elif state == 2:
            # In single-line comment, read characters util EOL.
            if char == '\n':
                position = pos.get_position_dict(current_comment, comment_start_pos)
                comment = Comment(current_comment, **position)
                comments.append(comment)
                current_comment = ''
                comment_start_pos = None
                state = 0
            else:
                current_comment += char
        elif state == 3:
            # In multi-line comment, add characters until '*' is
            # encountered.
            if char == '*':
                state = 4
            else:
                current_comment += char
        elif state == 4:
            # In multi-line comment with asterisk found. Determine if
            # comment is ending.
            if char == '/':
                position = pos.get_position_dict(current_comment, comment_start_pos)
                comment = Comment(current_comment, multiline=True, **position)
                comments.append(comment)
                current_comment = ''
                comment_start_pos = None
                state = 0
            else:
                current_comment += '*'
                # Care for multiple '*' in a row
                if char != '*':
                    current_comment += char
                    state = 3
        elif state == 5:
            # In string literal, expect literal end or escape character.
            if char == string_char:
                state = 0
            elif char == '\\':
                state = 6
        elif state == 6:
            # In string literal, escaping current char.
            state = 5
            if char == '\n':
                line_counter += 1

    # EOF.
    if state in (3, 4):
        raise UnterminatedCommentError()
    if state == 2:
        # Was in single-line comment. Create comment.
        position = pos.get_position_dict(current_comment, comment_start_pos)
        comment = Comment(current_comment, **position)
        comments.append(comment)
    return comments
# pylint: enable=line-too-long


# pylint: disable=line-too-long
def extract_c_like_comments(text: str) -> List[Comment]:
    """Extract comments from C-like languages.

    Works for:
        C99+
        C++
        Objective-C
        Java
        Php

    Single-line comments begin with '//' and continue to the end of line.
    Multi-line comments begin with '/*' and end with '*/' and can span
    multiple lines of code. If a multi-line comment does not terminate
    before EOF is reached, then an exception is raised.

    The string "*/*;q=0.1'," has been observed to cause multi-line
    termination issues in a php file.

    Args:

        text (str): Code as a string.

    Raises:
        UnterminatedCommentError: Unterminated multi-line comment.

    Returns:

        List[Comment]: List of Comment instances containing comments.
    """

    pos = PosCalculate(text=text)
    pattern = r"""
        (?P<literal> (\"([^\"\n])*\")+) |
        (?P<single> //(?P<single_content>.*)?$) |
        (?P<multi> /\*(?P<multi_content>(.|\n)*?)?\*/) |
        (?P<error> /\*(.*)?)
    """

    compiled = re.compile(pattern, re.VERBOSE | re.MULTILINE)

    # Get the index offset of each line
    lines_indexes: List[int] = list()
    for match in re.finditer(r"$", text, re.M):
        lines_indexes.append(match.start())

    comments: List[Comment] = list()
    for match in compiled.finditer(text):
        kind = match.lastgroup

        if kind == "single":
            comment_content = match.group("single_content")
            comment_start_pos = match.start("single_content")
            position = pos.get_position_dict(comment_content, comment_start_pos)
            comment = Comment(comment_content, **position)
            comments.append(comment)
        elif kind == "multi":
            comment_content = match.group("multi_content")
            comment_start_pos = match.start("multi_content")
            position = pos.get_position_dict(comment_content, comment_start_pos)
            comment = Comment(comment_content, multiline=True, **position)
            comments.append(comment)
        elif kind == "error":
            raise UnterminatedCommentError()

    return comments
# pylint: enable=line-too-long


# pylint: disable=line-too-long
def extract_html_xml_comments(text: str) -> List[Comment]:
    """Extract comments from HTML and XML.

    Comments cannot be nested.

    Args:

        text (str): Code as a string.

    Raises:
        UnterminatedCommentError: Unterminated multi-line comment.

    Returns:

        List[Comment]: List of Comment instances containing comments.
    """

    pos = PosCalculate(text=text)
    pattern = r"""
        (?P<literal> (\"([^\"\n])*\")+) |
        (?P<single> <!--(?P<single_content>.*?)-->) |
        (?P<multi> <!--(?P<multi_content>(.|\n)*?)?-->) |
        (?P<error> <!--(.*)?)
    """
    compiled = re.compile(pattern, re.VERBOSE | re.MULTILINE)

    lines_indexes = []
    for match in re.finditer(r"$", text, re.M):
        lines_indexes.append(match.start())

        comments = []
    for match in compiled.finditer(text):
        kind = match.lastgroup

        if kind == "single":
            comment_content = match.group("single_content")
            comment_start_pos = match.start("single_content")
            position = pos.get_position_dict(comment_content, comment_start_pos)
            comment = Comment(comment_content, **position)
            comments.append(comment)
        elif kind == "multi":
            comment_content = match.group("multi_content")
            comment_start_pos = match.start("single_content")
            position = pos.get_position_dict(comment_content, comment_start_pos)
            comment = Comment(comment_content, multiline=True, **position)
            comments.append(comment)
        elif kind == "error":
            raise UnterminatedCommentError()

    return comments
# pylint: enable=line-too-long


def main():
    """Main."""

    # filename = "tests/data/python/sample12.py"
    # filename = "tests/data/javascript/javascript_3.js"
    # filename = "tests/data/ruby/sample1.rb"
    filename = "tests/data/bash/bash_1.sh"
    with open(filename, 'r', encoding='utf-8') as f:
        data = f.read()

    # comments = extract_python_comments(data)
    # comments = extract_javascript_comments(data)
    # comments = extract_ruby_comments(data)
    comments = extract_shell_comments(data)

    for comment in comments:
        print(comment)
        print("=" * 80)

    print("", end='')

if __name__ == "__main__":
    main()
