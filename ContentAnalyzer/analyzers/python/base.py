"""Python Base"""

from typing import List
import attr

from ContentAnalyzer.base import KeyValuePair

@attr.s(kw_only=True, slots=True)
class PythonAnalyzer:
    """PythonAnalyzer."""

    kvps: List[KeyValuePair] = attr.ib(factory=list)
    text = attr.ib(factory=list)


    def analyze(self, content: str) -> None:
        """Analyze content.

        Args:

            content (str): Content to analyze.
        """

        import parso
        from ContentAnalyzer.analyzers.python.parser import Walker, Visitor

        code = parso.parse(content)
        walker = Walker(code)
        visitor = Visitor(text=content)
        walker.accept(visitor)
        self.kvps = visitor.get_matches()
        self.text = visitor.get_comments()


    def get_kvps(self) -> List[KeyValuePair]:
        """Get a list of KeyValuePairs.

        Returns:

            list: List of KeyValuePairs.
        """
        return self.kvps.copy()


    def get_text(self):
        return self.text.copy()

# def main():
#     """Main."""

#     filename = "tests/data/python/sample4.py"
#     content = open(filename, 'r', encoding='utf-8').read()
#     # content = TEXT

#     doc = PythonAnalyzer()
#     doc.analyze(content)

#     for kvp in doc.get_kvps():
#         print(kvp.to_dict())

#     print("", end='')


# if __name__ == "__main__":
#     main()
