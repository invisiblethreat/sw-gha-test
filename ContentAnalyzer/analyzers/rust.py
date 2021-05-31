"""Rust analyzer."""

from typing import List

import attr
from pygments.lexers.rust import RustLexer

from ContentAnalyzer.analyzers.utils import State, get_column_start_end
from ContentAnalyzer.base import NewKeyValuePair

__all__ = ['RustAnalyzer']

@attr.s(kw_only=True, slots=True)
class RustAnalyzer:
    """RustAnalyzer."""

    kvps: List[NewKeyValuePair] = attr.ib(factory=list)

    # pylint: disable=unused-argument
    def analyze(self, content: str) -> None:
        """Analyze content.

        Args:
            content (str): Content to analyze.
        """

        lexer = RustLexer()
        tokens = list(lexer.get_tokens_unprocessed(content))

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

#     filename = "tests/data/rust/sample1.rs"

#     with open(filename, 'r', encoding='utf-8') as f:
#         bt = time.time()
#         doc = RustAnalyzer()
#         doc.analyze(f.read())
#         rt = round(time.time() - bt, 2)

#     for kvp in doc.get_kvps():
#         print(f"{kvp.key} => {kvp.value}")

#     print(f"Found {len(doc.kvps)} key/value pairs in {rt} seconds")
#     print("", end='')

# if __name__ == "__main__":
#     main()
