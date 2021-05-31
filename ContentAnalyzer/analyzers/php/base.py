"""Php analyzer."""

from typing import List

import attr

from ContentAnalyzer.analyzers.php.phpparser import parse
from ContentAnalyzer.base import NewKeyValuePair


@attr.s(kw_only=True, slots=True)
class PhpAnalyzer:
    """PhpAnalyzer."""

    kvps: List[NewKeyValuePair] = attr.ib(factory=list)

    # pylint: disable=unused-argument
    def analyze(self, content: str) -> None:
        """Analyze content.

        Args:
            content (str): Content to analyze.
        """

        parser_kvps = parse(content)

        for parser_kvp in parser_kvps:
            kv_pair = NewKeyValuePair(**parser_kvp)
            self.kvps.append(kv_pair)

    # pylint: enable=unused-argument

    def get_kvps(self) -> List[NewKeyValuePair]:
        """Get a list of KeyValuePairs.

        Returns:

            list: List of KeyValuePairs.
        """
        return self.kvps.copy()

def main():
    """Main."""

    import time

    # filename = "tests/data/php/sample5.php"
    filename = "utah-class.php"

    with open(filename, 'r', encoding='utf-8') as f:
        bt = time.time()
        doc = PhpAnalyzer()
        doc.analyze(f.read())
        rt = round(time.time() - bt, 2)

    print(f"Found {len(doc.kvps)} key/value pairs in {rt} seconds")
    print("", end='')

if __name__ == "__main__":
    main()
