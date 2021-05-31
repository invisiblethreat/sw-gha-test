"""pygments stuff"""

from typing import (Any, Callable, Dict, Iterable, List, Optional, Set, Tuple,
                    Union)

import pygments
from pygments.lexers.dotnet import CSharpLexer
from pygments.lexers.javascript import TypeScriptLexer
from pygments.lexers.shell import PowerShellLexer, BashLexer
from pygments.lexers.go import GoLexer
from pygments.lexers.rust import RustLexer
from pygments.lexers.jvm import KotlinLexer
from pygments.lexers.jvm import ScalaLexer


class State:
    """State"""

    def __init__(self):
        self.key: str = None
        self.value: str = None
        self.start_pos: int = None
        self.end_pos: int = None
        self.start_line: int = None
        self.end_line: int = None
        self.start_column: int = None
        self.end_column: int = None
        self.have_operator: bool = False
        # self.line_number_state: int = 0
        self.lineno: int = 1
        self.pending_line_count: int = 0

    def update_linenumber_state(self, value: str):
        """Update linenumber state"""
        self.lineno += self.pending_line_count
        line_count = str(value).count("\n")
        self.pending_line_count = line_count
        # self.lineno += line_count
        # self.pending_line_count = 0

    def set_key(self, key: str):
        """Set key value"""
        self.key = key

    def set_value(self, value: str, strip_quotes: bool = False):
        """Set value's value.

        Args:

            value (str): Value for value.
            strip_quotes (bool, optional): Strip leading and ending quotes. Defaults to False.
        """
        if strip_quotes:
            if value.startswith(("\"", "'")):
                value = value[1:]
            if value.endswith(("\"", "'")):
                value = value[0:-1]
        self.start_line = self.lineno
        self.end_line = self.lineno + max(0, value.count("\n") - 1)
        self.value = value

    def set_pos(self, start_pos: int, end_pos: int = None):
        """Set starting pos.

        Can't set starting pos before setting value!

        Args:

            start_pos (int): Starting position.
            end_pos (int, optional): Ending position. Defaults to None.
        """
        self.start_pos = start_pos
        if isinstance(end_pos, int):
            self.end_pos = end_pos
        else:
            if self.value is None:
                raise ValueError("Must set a value for value before setting pos if not providing an end_pos!")
            self.end_pos = start_pos + len(self.value)

    def reset_state(self):
        """Reset state"""

        self.key = None
        self.value = None
        self.start_pos = None
        self.end_pos = None
        self.start_line = None
        self.end_line = None
        self.start_column = None
        self.end_column = None
        self.have_operator = False

    def ready_for_value(self) -> bool:
        """Whether or not state is ready to accept a value.

        This usually means we have a key and an operator."""

        if self.key is None or not self.have_operator:
            return False
        return True

    def ready_for_operator(self) -> bool:
        """Whether or not state is ready to accept an operator.

        This usually means we have a key and are pending an operator."""

        if self.key is None:
            return False
        return True

    def to_dict(self):
        """To dict"""

        return {
            'key': self.key,
            'value': self.value,
            'start_pos': self.start_pos,
            'end_pos': self.end_pos,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'start_column': self.start_column,
            'end_column': self.end_column,
        }

class GoState(State):
    """State"""

    def __init__(self):
        super().__init__()
        self.has_second_var: bool = False

    def reset_state(self):
        """Reset state"""

        super().reset_state()
        self.has_second_var = False

    def ready_for_value(self) -> bool:
        """Whether or not state is ready to accept a value.

        This usually means we have a key and an operator."""

        if self.key is None:
            return False
        if self.have_operator:
            return True
        return False

def get_column_start_end(text: str, kvp: Dict) -> Dict:
    """Get column start and end from text from a kvp"""

    start_line = text.rfind('\n', 0, kvp['start_pos']) + 1
    start_column = (kvp['start_pos'] - start_line) + 1
    end_column = len(kvp['value'].rstrip().split('\n')[-1]) + start_column
    positions = dict(start_column=start_column, end_column=end_column)
    return positions

def parse_powershell(text: str):
    """Parse powershell"""

    lexer = PowerShellLexer()
    tokens = list(lexer.get_tokens_unprocessed(text))

    kvps = list()
    state = State()

    for pos, token, value in tokens:
        token_kind = str(token)
        if token_kind == "Token.Text":
            continue

        if token_kind == "Token.Name.Variable" or token_kind == "Token.Name.Builtin" or (token_kind == "Token.Name" and value.startswith('-')):
            state.reset_state()
            state.set_key(value)
            continue
        elif token_kind == "Token.Punctuation" and state.ready_for_operator():
            if value != "=":
                # Not variable assignment so reset state
                state.reset_state()
            else:
                state.have_operator = True
            continue
        elif token_kind == "Token.Literal.String.Double" and value == "\"":
            # Skip this since it is probably just surrounding quotes of string
            continue
        elif token_kind == "Token.Literal.String.Double" and state.ready_for_value():
            state.set_value(value, strip_quotes=False)
            state.set_pos(pos)
            kvp = state.to_dict()
            kvps.append(kvp)

            # Reset state
            state.reset_state()
            continue
        else:
            # Reset state
            state.reset_state()

    return kvps

def parse_csharp(text: str):
    """Parse csharp"""

    lexer = CSharpLexer()
    tokens = list(lexer.get_tokens_unprocessed(text))

    kvps = list()
    state = State()

    for pos, token, value in tokens:
        token_kind = str(token)
        if token_kind == "Token.Text":
            continue

        if token_kind == "Token.Name" or token_kind == "Token.Keyword":
            state.reset_state()
            state.set_key(value)
            continue
        elif token_kind == "Token.Punctuation" and state.ready_for_operator():
            if value not in ("=", "("):
                # Not variable assignment so reset state
                state.reset_state()
            else:
                state.have_operator = True
            continue
        elif token_kind == "Token.Literal.String" and state.ready_for_value():
            # Need to add 1 to the position since the string will start and end with quotes
            state.set_value(value, strip_quotes=True)
            state.set_pos(pos + 1)
            kvp = state.to_dict()
            kvps.append(kvp)

            # Reset state
            state.reset_state()
            continue
        else:
            # Reset state
            state.reset_state()

    return kvps


def parse_typescript(text: str):
    """Parse typescript"""

    lexer = TypeScriptLexer()
    tokens = list(lexer.get_tokens_unprocessed(text))

    kvps = list()
    state = State()

    for pos, token, value in tokens:
        token_kind = str(token)
        if token_kind == "Token.Text":
            continue

        if token_kind == "Token.Name.Other" or token_kind == "Token.Keyword":
            state.reset_state()
            state.set_key(value)
            continue
        elif token_kind == "Token.Operator" or (token_kind == "Token.Punctuation" and value == "(") and state.ready_for_operator():
            # TODO: Track state of paranthesis () to try and determine what parameters
            # are string arguments to function calls.
            if value not in ("=", "(", ":"):
                # Not variable assignment so reset state
                state.reset_state()
            else:
                state.have_operator = True
            continue
        elif token_kind.startswith("Token.Literal.String") and state.ready_for_value():
            if not token_kind.endswith(('.Single', '.Double')):
                raise ValueError(f"Don't know how to strip char from token {token_kind} with value {value}")

            # Need to add 1 to the position since the string will start and end with quotes
            state.set_value(value, strip_quotes=True)
            state.set_pos(pos + 1)
            kvp = state.to_dict()
            kvps.append(kvp)

            # Reset state
            state.reset_state()
            continue
        else:
            # Reset state
            state.reset_state()

    return kvps

def parse_go(text: str):
    """Parse go"""

    lexer = GoLexer()
    tokens = list(lexer.get_tokens_unprocessed(text))

    kvps = list()
    state = GoState()

    for pos, token, value in tokens:
        token_kind = str(token)
        if token_kind == "Token.Text":
            continue

        if token_kind == "Token.Name.Other":
            if state.has_second_var and not state.ready_for_value():
                # We're the second variable and we're not waiting for a value
                continue

            state.reset_state()
            state.set_key(value)
            continue

        elif token_kind == "Token.Punctuation" and state.ready_for_operator():
            if value not in ("(", ","):
                # Not string usage in function
                state.reset_state()
                continue

            if value == "(":
                state.have_operator = True
            elif value == ",":
                # This could be an error check like:
                # someVar, err := someFunc("value")
                # So let's not reset state
                state.has_second_var = True
            else:
                raise ValueError(f"Don't know how to process token {token} with value {value} for operator state")
            continue

        elif token_kind == "Token.Operator" and state.ready_for_operator():
            if value != ":=":
                # Not an assignment operator
                state.reset_state()
                continue
            state.have_operator = True
            continue

        elif token_kind == "Token.Literal.String" and state.ready_for_value():
            # Need to add 1 to the position since the string will start and end with quotes
            state.set_value(value, strip_quotes=True)
            state.set_pos(pos + 1)
            kvp = state.to_dict()
            kvps.append(kvp)

            # Reset state
            state.reset_state()
            continue
        else:
            # Reset state
            state.reset_state()

    return kvps

def parse_rust(text: str):
    """Parse rust"""

    lexer = RustLexer()
    tokens = list(lexer.get_tokens_unprocessed(text))

    kvps = list()
    state = State()

    for pos, token, value in tokens:
        token_kind = str(token)
        if token_kind == "Token.Text.Whitespace":
            continue

        if token_kind == "Token.Name" or token_kind == "Token.Keyword":
            state.reset_state()
            state.set_key(value)
            continue
        elif token_kind == "Token.Operator" and state.ready_for_operator():
            # Just ignore this
            continue
        elif token_kind == "Token.Punctuation" or (token_kind == "Token.Text" and value == ":") and state.ready_for_operator():
            if value not in ("=", "(", ":"):
                # Not variable assignment so reset state
                state.reset_state()
            else:
                state.have_operator = True
            continue
        elif token_kind == "Token.Literal.String" and value == "\"":
            # Skip this since it is probably just surrounding quotes of string
            continue
        elif token_kind == "Token.Literal.String" and state.ready_for_value():
            # Need to add 1 to the position since the string will start and end with quotes
            state.set_value(value, strip_quotes=False)
            state.set_pos(pos)
            kvp = state.to_dict()
            kvps.append(kvp)

            # Reset state
            state.reset_state()
            continue
        else:
            # Reset state
            state.reset_state()

    return kvps

def parse_bash(text: str):
    """Parse bash"""

    lexer = BashLexer()
    tokens = list(lexer.get_tokens_unprocessed(text))

    # This captures strings quite well but does not fare well when text is involved.
    # For example, the following works as expected:
    # export SLACK_TOKEN='xoxp-480290906294-478890564626-498177603287-732c8a87dec3b7d21a2e8411f5008a66'
    # But the following is not tracked because its token is "Token.Text":
    # export SLACK_TOKEN=xoxp-480290906294-478890564626-493193214482-ff1857265064ba34659c3c09c3fa9fc1

    kvps = list()
    state = State()

    for pos, token, value in tokens:
        token_kind = str(token)
        if token_kind == "Token.Text":
            continue

        if token_kind == "Token.Name.Variable" or token_kind == "Token.Name.Builtin" or (token_kind == "Token.Name" and value.startswith('-')):
            state.reset_state()
            state.set_key(value)
            continue
        elif token_kind == "Token.Operator" and state.ready_for_operator():
            if value != "=":
                # Not variable assignment so reset state
                state.reset_state()
            else:
                state.have_operator = True
            continue
        elif token_kind.startswith("Token.Literal.String.") and value in ("\"", "'"):
            # Skip this since it is probably just surrounding quotes of string
            continue
        elif token_kind.startswith("Token.Literal.String.") and state.ready_for_value():
            state.set_value(value, strip_quotes=False)
            state.set_pos(pos)
            kvp = state.to_dict()
            kvps.append(kvp)

            # Reset state
            state.reset_state()
            continue
        else:
            # Reset state
            state.reset_state()

    return kvps

def parse_kotlin(text: str):
    """Parse kotlin"""

    lexer = KotlinLexer()
    tokens = list(lexer.get_tokens_unprocessed(text))

    kvps = list()
    state = State()

    for pos, token, value in tokens:
        token_kind = str(token)
        if token_kind == "Token.Text":
            continue

        if token_kind in ("Token.Name", "Token.Keyword", "Token.Name.Function", "Token.Name.Property"):
            if token_kind == "Token.Name" and value == "String":
                # Want to avoid these situations:
                # fun hello(name: String = "world"): String {
                continue
            state.reset_state()
            state.set_key(value)
            continue
        elif token_kind == "Token.Punctuation" and state.ready_for_operator():
            if value not in ("=", "(", ":"):
                # Not variable assignment so reset state
                state.reset_state()
            else:
                state.have_operator = True
            continue
        elif token_kind == "Token.Literal.String" and state.ready_for_value():
            # Need to add 1 to the position since the string will start and end with quotes
            state.set_value(value, strip_quotes=True)
            state.set_pos(pos + 1)
            kvp = state.to_dict()
            kvps.append(kvp)

            # Reset state
            state.reset_state()
            continue
        else:
            # Reset state
            state.reset_state()

    return kvps

def parse_scala(text: str):
    """Parse scala"""

    lexer = ScalaLexer()
    tokens = list(lexer.get_tokens_unprocessed(text))

    kvps = list()
    state = State()

    for pos, token, value in tokens:
        state.update_linenumber_state(value)
        token_kind = str(token)
        if token_kind == "Token.Text":
            continue

        if token_kind in ("Token.Name", "Token.Name.Class"):
            if token_kind == "Token.Name" and value == "String":
                # Want to avoid these situations:
                # fun hello(name: String = "world"): String {
                continue
            state.reset_state()
            state.set_key(value)
            continue
        elif token_kind in ("Token.Operator", "Token.Keyword") and state.ready_for_operator():
            if value not in ("=", "(", ":"):
                # Not variable assignment so reset state
                state.reset_state()
            else:
                state.have_operator = True
            continue
        elif token_kind == "Token.Literal.String" and state.ready_for_value():
            # Need to add 1 to the position since the string will start and end with quotes
            state.set_value(value, strip_quotes=True)
            state.set_pos(pos + 1)
            kvp = state.to_dict()
            line_positions = get_column_start_end(text, kvp)
            kvp.update(line_positions)
            kvps.append(kvp)

            # Reset state
            state.reset_state()
            continue
        else:
            # Reset state
            state.reset_state()

    return kvps



def main():
    """Main."""

    # filename = "sample1.ps1"
    # filename = "sample1.cs"
    # filename = "sample1.tsx"
    # filename = "sample1.go"
    # filename = "sample1.rs"
    # filename = "sample1.sh"
    # filename = "sample1.kt"
    filename = "tests/data/scala/sample1.scala"

    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()

    kvps = parse_scala(text)

    print("", end='')

if __name__ == "__main__":
    main()
