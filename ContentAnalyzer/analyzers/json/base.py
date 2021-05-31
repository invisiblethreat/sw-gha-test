"""JSON analyzer."""

from typing import List
import attr

from ContentAnalyzer.lexers import KeyValuePair
from ContentAnalyzer.analyzers.json.jsonparser import parse


@attr.s(kw_only=True, slots=True)
class JsonAnalyzer:
    """JsonAnalyzer."""

    kvps: List[KeyValuePair] = attr.ib(factory=list)

    # pylint: disable=unused-argument
    def analyze(self, content: str) -> None:
        """Analyze content.

        Args:
            content (str): Content to analyze.
        """

        parser_kvps = parse(content)

        for parser_kvp in parser_kvps:
            kv_pair = KeyValuePair(raw=parser_kvp)
            self.kvps.append(kv_pair)

    # pylint: enable=unused-argument

    def get_kvps(self) -> List[KeyValuePair]:
        """Get a list of KeyValuePairs.

        Returns:

            list: List of KeyValuePairs.
        """
        return self.kvps.copy()

# def main():
#     """Main."""

#     # import time

#     # filename = "local_data/jobs-medical_coding_jobs.json"

#     # with open(filename, 'r', encoding='utf-8') as f:
#     #     bt = time.time()
#     #     doc = JsonAnalyzer()
#     #     doc.analyze(f.read())
#     #     rt = round(time.time() - bt, 2)

#     # print(f"Found {len(doc.kvps)} key/value pairs in {rt} seconds")
#     # print("", end='')

# if __name__ == "__main__":
#     main()
