"""Powershell analyzer."""

from typing import List

import attr
from pygments.lexers.shell import PowerShellLexer

from ContentAnalyzer.analyzers.utils import State, get_column_start_end
from ContentAnalyzer.base import NewKeyValuePair

__all__ = ['PowershellAnalyzer']

@attr.s(kw_only=True, slots=True)
class PowershellAnalyzer:
    """PowershellAnalyzer."""

    kvps: List[NewKeyValuePair] = attr.ib(factory=list)

    # pylint: disable=unused-argument
    def analyze(self, content: str) -> None:
        """Analyze content.

        Args:
            content (str): Content to analyze.
        """

        lexer = PowerShellLexer()
        tokens = list(lexer.get_tokens_unprocessed(content))

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
                line_positions = get_column_start_end(content, kvp)
                kvp.update(line_positions)
                kvps.append(kvp)

                # Reset state
                state.reset_state()
                continue
            else:
                # Reset state
                state.reset_state()

        for parser_kvp in kvps:
            kv_pair = NewKeyValuePair(**parser_kvp)
            self.kvps.append(kv_pair)

    # pylint: enable=unused-argument

    def get_kvps(self) -> List[NewKeyValuePair]:
        """Get a list of KeyValuePairs.

        Returns:

            list: List of KeyValuePairs.
        """
        return self.kvps.copy()

# def main():
#     """Main."""

#     import time

#     filename = "tests/data/powershell/sample1.ps1"

#     with open(filename, 'r', encoding='utf-8') as f:
#         bt = time.time()
#         doc = PowershellAnalyzer()
#         doc.analyze(f.read())
#         rt = round(time.time() - bt, 2)

#     for kvp in doc.get_kvps():
#         print(f"{kvp.key} => {kvp.value}")

#     print(f"Found {len(doc.kvps)} key/value pairs in {rt} seconds")
#     print("", end='')

# if __name__ == "__main__":
#     main()
