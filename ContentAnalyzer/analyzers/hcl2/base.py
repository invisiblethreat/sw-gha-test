"""Hcl2 analyzer."""

from typing import List

import attr

from ContentAnalyzer.analyzers.hcl2.walker import walk
from ContentAnalyzer.base import NewKeyValuePair


@attr.s(kw_only=True, slots=True)
class Hcl2Analyzer:
    """Hcl2Analyzer."""

    kvps: List[NewKeyValuePair] = attr.ib(factory=list)

    # pylint: disable=unused-argument
    def analyze(self, content: str) -> None:
        """Analyze content.

        Args:
            content (str): Content to analyze.
        """

        parser_kvps = walk(content)

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

# def main():
#     """Main."""

#     import time

#     filename = "tests/data/hcl2/sample2.tf"

#     with open(filename, 'r', encoding='utf-8') as f:
#         bt = time.time()
#         doc = Hcl2Analyzer()
#         doc.analyze(f.read())
#         rt = round(time.time() - bt, 2)

#     for kvp in doc.get_kvps():
#         print(f"{kvp.key} => {kvp.value}")

#     print(f"Found {len(doc.kvps)} key/value pairs in {rt} seconds")
#     print("", end='')

# if __name__ == "__main__":
#     main()
