"""Simple Json analyzer."""

from ContentAnalyzer.lexers import Document, KeyValuePair

class SimpleJsonAnalyzer(Document):
    """SimpleJsonAnalyzer"""

    # pylint: disable=unused-argument
    def analyze(self, content):
        """Analyze content.

        Args:
            content (str): Content to analyze.
        """

        self.set_lexer("SimpleJsonLexer")

        self.parse(content)

        left_side = None
        right_side = None
        for token in self.all_tokens:
            if token.kind == "analyzer.Key":
                left_side = token
            elif token.kind == "analyzer.Value":
                right_side = token
                kv_pair = KeyValuePair.from_tokens(left_side, right_side)
                self.kvps.append(kv_pair)
                left_side = None
                right_side = None
            else:
                raise ValueError("Unknown token kind '%s'" % token.kind)

    # pylint: enable=unused-argument

# def main():
#     """Main."""

#     doc = SimpleJsonAnalyzer()
#     doc.analyze(TEXT2)

#     # kinds = doc.get_token_kinds()
#     # print("expected = [")
#     # for n in kinds:
#     #     print("    '%s'," % n)
#     # print("]")

#     # print("expected = {")
#     # for kind in kinds: 
#     #     print("    '%s': %s," % (kind, len(list(doc.get_tokens(kind=kind))))) 
#     # print("}")

#     # for n in doc.get_kvps(as_kvp=True):
#     #     print(n)

#     print(f"Found {len(doc.kvps)} key/value pairs")
#     # print("breakpoint")

# if __name__ == "__main__":
#     main()
