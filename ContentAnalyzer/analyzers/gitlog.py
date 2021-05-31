"""Git log file analyzer."""

from ContentAnalyzer.lexers import Document

class GitLogAnalyzer(Document):
    """GitLogAnalyzer"""

    # pylint: disable=unused-argument
    def analyze(self, content):
        """Analyze content.

        If 'content' is None then an attempt will be made to read
        the contents of the file in the 'filename' property.

        Args:
            content (str, optional): Defaults to None. Content to analyze.
        """

        self.set_lexer("GitLogLexer")

        self.parse(content)

    # pylint: enable=unused-argument

def main():
    """Main."""

    doc = GitLogAnalyzer()
    with open("tests/data/git/HEAD", "r", encoding='utf-8') as f:
        content = f.read()
    doc.analyze(content)

    kinds = doc.get_token_kinds()
    print("expected = [")
    for n in kinds:
        print("    '%s'," % n)
    print("]")

    print("expected = {")
    for kind in kinds:
        print("    '%s': %s," % (kind, len(list(doc.get_tokens(kind=kind)))))
    print("}")

    for n in doc.get_kvps():
        print(n)

    print("breakpoint")

if __name__ == "__main__":
    main()
