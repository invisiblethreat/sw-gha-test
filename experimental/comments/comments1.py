"""Extract comments from code"""

import io
import tokenize
import re
from bisect import bisect_left
from typing import List


class Error(Exception):
    """Base Error class for all comment parsers."""


class FileError(Error):
    """Raised if there is an issue reading a given file."""


class UnterminatedCommentError(Error):
    """Raised if an Unterminated multi-line comment is encountered."""


class Comment:
    """Comment."""

    def __str__(self):
        return self._text

    def __repr__(self):
        return f"Comment({self.text}, {self._line_number}, {self._multiline})"

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self.__dict__ == other.__dict__:
                return True
        return False


    def __init__(self, text: str, line_number: int, multiline: bool = False, start_pos: int = 0):
        """Comment.

        Args:

            text (str): Comment content text.
            line_number (int): Line number of comment
            multiline (bool, optional): Comment is multiline. Defaults to False.
            start_pos (int, optional): Absolute starting position of comment in text.

        """
        self._text = text
        self._line_number = line_number
        self._multiline = multiline
        self._start_pos = start_pos
        self._end_pos = start_pos + len(text)


    @property
    def text(self) -> str:
        """Get content's text.

        Returns:

            str: Content of comment's text.
        """
        return self._text


    @property
    def line_number(self) -> int:
        """Get content's line number.

        Returns:

            int: Line number of content.
        """
        return self._line_number


    @property
    def is_multiline(self) -> bool:
        """Is comment multi line?

        Returns:

            bool: Whether or not comment is multi line.
        """
        return self._multiline


    @property
    def start_pos(self) -> int:
        """Starting position of text.

        Returns:

            int: Starting position of comment.
        """
        return self._start_pos


    @property
    def end_pos(self) -> int:
        """Ending position of text.

        Returns:

            int: Ending position of comment.
        """
        return self._end_pos


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
    lengths = dict()
    start_offsets = {0: 0}
    current_offset = 0
    for i, n in enumerate(text.split('\n')):
        line_length = len(n)
        lengths[i] = line_length
        start_offsets[i + 1] = current_offset + line_length
        current_offset += line_length

    comments = list()
    tokens = tokenize.tokenize(io.BytesIO(text.encode()).readline)
    for toknum, tokstring, tokloc, _, _ in tokens:
        if toknum is tokenize.COMMENT:
            # Removes leading '#' character
            tokstring = tokstring[1:]
            comment_start_pos = start_offsets[tokloc[0] - 1] + tokloc[1]
            comments.append(Comment(tokstring, tokloc[0], multiline=False, start_pos=comment_start_pos))
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
    state = 0
    current_comment = ''
    comments = list()
    line_counter = 1
    comment_start = 1
    comment_start_pos = 0
    string_char = ''
    for i, char in enumerate(text):
        if state == 0:
            # Waiting for comment start character or beginning of string
            if char == '/':
                state = 1
            elif char in ('"', "'"):
                string_char = char
                state = 5
        elif state == 1:
            # Found comment start character, classify next character and
            # determine if single or multi-line comment
            if char == '/':
                state = 2
            elif char == '*':
                comment_start = line_counter
                comment_start_pos = i
                state = 3
            else:
                state = 0
        elif state == 2:
            # In single-line comment, read characters until EOL
            if char == '\n':
                comment = Comment(current_comment, line_counter, start_pos=comment_start_pos)
                comments.append(comment)
                current_comment = ''
                state = 0
            else:
                current_comment += char
        elif state == 3:
            # In multi-line comment, add characters until '*' is encountered
            if char == '*':
                state = 4
            else:
                current_comment += char
        elif state == 4:
            # In multi-line comment with asterisk found. Determine if
            # comment is ending
            if char == '/':
                comment = Comment(current_comment, comment_start, multiline=True)
                comments.append(comment)
                current_comment = ''
                state = 0
            else:
                current_comment += '*'
                # Care for multiple '*' in a row
                if char != '*':
                    current_comment += char
                    state = 3
        elif state == 5:
            # In string literal, expect literal end or escape character
            if char == string_char:
                state = 0
            elif char == '\\':
                state = 6
        elif state == 6:
            # In string literal, escaping current char
            state = 5
            if char == '\n':
                line_counter += 1

    # EOF
    if state in (3, 4):
        raise UnterminatedCommentError()
    if state == 2:
        # Was in single-line comment. Create comment.
        comment = Comment(current_comment, line_counter)
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

    pattern = r"""
        (?P<literal> ([\"'])((?:\\\2|(?:(?!\2)).)*)(\2)) |
        (?P<single> \#(?P<single_content>.*?)$)
    """
    compiled = re.compile(pattern, re.VERBOSE | re.MULTILINE)

    lines_indexes = list()
    for match in re.finditer(r"$", text, re.M):
        lines_indexes.append(match.start())

    comments = list()
    for match in compiled.finditer(text):
        kind = match.lastgroup

        start_character = match.start()
        line_no = bisect_left(lines_indexes, start_character)

        if kind == "single":
            comment_content = match.group("single_content")
            comment = Comment(comment_content, line_no + 1, start_pos=match.start("single_content"))
            comments.append(comment)

    return comments


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
    state = 0
    string_char = ''
    current_comment = ''
    comments = []
    line_counter = 1
    comment_start_pos = None
    for i, char in enumerate(text):
        if state == 0:
            # Waiting for comment start character, beginning of string,
            # or escape character.
            if char == '#':
                state = 1
            elif char in ('"', "'"):
                string_char = char
                state = 2
            elif char == '\\':
                state = 4
        elif state == 1:
            # Found comment start character. Read comment until EOL.
            if char == '\n':
                comment = Comment(current_comment, line_counter, start_pos=comment_start_pos)
                comments.append(comment)
                current_comment = ''
                comment_start_pos = None
                state = 0
            else:
                if comment_start_pos is None:
                    comment_start_pos = i
                current_comment += char
        elif state == 2:
            # In string literal, wait for string end or escape char.
            if char == string_char:
                state = 0
            elif char == '\\':
                state = 3
        elif state == 3:
            # Escaping current char, inside of string.
            state = 2
        elif state == 4:
            # Escaping current char, outside of string.
            state = 0
        if char == '\n':
            line_counter += 1

    # EOF.
    if state == 1:
        # Was in single line comment. Create comment.
        comment = Comment(current_comment, line_counter)
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
    state = 0
    current_comment = ''
    comments = list()
    line_counter = 1
    comment_start = 1
    comment_start_pos = None
    string_char = ''
    for i, char in enumerate(text):
        if state == 0:
            # Waiting for comment start character or beginning of
            # string or rune literal
            if char == '/':
                state = 1
            elif char in ('"', "'", '`'):
                string_char = char
                state = 5
        elif state == 1:
            # Found comment start character, classify next character and
            # determine if single or multi-line comment
            if char == '/':
                state = 2
            elif char == '*':
                comment_start = line_counter
                comment_start_pos = i
                state = 3
            else:
                state = 0
        elif state == 2:
            # In single-line comment, read characters util EOL
            if char == '\n':
                comment = Comment(current_comment, line_counter, start_pos=comment_start_pos)
                comments.append(comment)
                current_comment = ''
                comment_start_pos = None
                state = 0
            else:
                current_comment += char
        elif state == 3:
            # In multi-line comment, add characters until '*' is encountered
            if char == '*':
                state = 4
            else:
                current_comment += char
        elif state == 4:
            # In multi-line comment with asterisk found. Determine if comment is ending
            if char == '/':
                comment = Comment(current_comment, comment_start, multiline=True, start_pos=comment_start_pos)
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
            # In string literal, expect literal end or escape character
            if char == string_char:
                state = 0
            elif char == '\\':
                state = 6
        elif state == 6:
            # In string literal, escaping current char
            state = 5
            if char == '\n':
                line_counter += 1

    # EOF
    if state in (3, 4):
        raise UnterminatedCommentError()
    if state == 2:
        # Was in single-line comment. Create comment.
        comment = Comment(current_comment, line_counter, start_pos=comment_start_pos)
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

    Single-line comments begin with '//' and continue to the end of line.
    Multi-line comments begin with '/*' and end with '*/' and can span
    multiple lines of code. If a multi-line comment does not terminate
    before EOF is reached, then an exception is raised.

    Args:

        text (str): Code as a string.

    Raises:
        UnterminatedCommentError: Unterminated multi-line comment.

    Returns:

        List[Comment]: List of Comment instances containing comments.
    """

    pattern = r"""
        (?P<literal> (\"([^\"\n])*\")+) |
        (?P<single> //(?P<single_content>.*)?$) |
        (?P<multi> /\*(?P<multi_content>(.|\n)*?)?\*/) |
        (?P<error> /\*(.*)?)
    """

    compiled = re.compile(pattern, re.VERBOSE | re.MULTILINE)

    lines_indexes = list()
    for match in re.finditer(r"$", text, re.M):
        lines_indexes.append(match.start())

    comments = list()
    for match in compiled.finditer(text):
        kind = match.lastgroup

        start_character = match.start()
        line_no = bisect_left(lines_indexes, start_character)

        if kind == "single":
            comment_content = match.group("single_content")
            comment = Comment(comment_content, line_no + 1, start_pos=match.group("single_content"))
            comments.append(comment)
        elif kind == "multi":
            comment_content = match.group("multi_content")
            comment = Comment(comment_content, line_no + 1, multiline=True, start_pos=match.group("multi_content"))
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

    pattern = r"""
        (?P<literal> (\"([^\"\n])*\")+) |
        (?P<single> <!--(?P<single_content>.*?)-->) |
        (?P<multi> <!--(?P<multi_content>(.|\n)*?)?-->) |
        (?P<error> <!--(.*)?)
    """
    compiled = re.compile(pattern, re.VERBOSE | re.MULTILINE)

    lines_indexes = list()
    for match in re.finditer(r"$", text, re.M):
        lines_indexes.append(match.start())

        comments = list()
    for match in compiled.finditer(text):
        kind = match.lastgroup

        start_character = match.start()
        line_no = bisect_left(lines_indexes, start_character)

        if kind == "single":
            comment_content = match.group("single_content")
            comment = Comment(comment_content, line_no + 1, start_pos=match.group("single_content"))
            comments.append(comment)
        elif kind == "multi":
            comment_content = match.group("multi_content")
            comment = Comment(comment_content, line_no + 1, multiline=True, start_pos=match.group("multi_content"))
            comments.append(comment)
        elif kind == "error":
            raise UnterminatedCommentError()

    return comments
# pylint: enable=line-too-long



def main():
    """Main."""

    # filename = "tests/data/python/sample12.py"
    # filename = "tests/data/javascript/javascript_3.js"
    filename = "tests/data/ruby/sample1.rb"
    # filename = "tests/data/bash/bash_1.sh"
    with open(filename, 'r', encoding='utf-8') as f:
        data = f.read()

    # comments = extract_python_comments(data)
    # comments = extract_javascript_comments(data)
    comments = extract_ruby_comments(data)
    # comments = extract_shell_comments(data)

    for comment in comments:
        print(comment.start_pos)
        print("=" * 80)

    print("", end='')

if __name__ == "__main__":
    main()
