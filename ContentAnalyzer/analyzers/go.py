"""Go analyzer."""

from typing import List

import attr
from pygments.lexers.go import GoLexer

from ContentAnalyzer.analyzers.utils import GoState, get_column_start_end
from ContentAnalyzer.base import NewKeyValuePair

__all__ = ['GoAnalyzer']

@attr.s(kw_only=True, slots=True)
class GoAnalyzer:
    """GoAnalyzer."""

    kvps: List[NewKeyValuePair] = attr.ib(factory=list)

    # pylint: disable=unused-argument
    def analyze(self, content: str) -> None:
        """Analyze content.

        Args:
            content (str): Content to analyze.
        """

        lexer = GoLexer()
        tokens = list(lexer.get_tokens_unprocessed(content))

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

#     filename = "tests/data/go/sample1.go"

#     with open(filename, 'r', encoding='utf-8') as f:
#         bt = time.time()
#         doc = GoAnalyzer()
#         doc.analyze(f.read())
#         rt = round(time.time() - bt, 2)

#     for kvp in doc.get_kvps():
#         print(f"{kvp.key} => {kvp.value}")

#     print(f"Found {len(doc.kvps)} key/value pairs in {rt} seconds")
#     print("", end='')

# if __name__ == "__main__":
#     main()
