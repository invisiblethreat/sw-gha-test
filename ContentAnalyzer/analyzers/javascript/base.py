"""Javascript Base"""

from typing import List

import attr
import esprima

from ContentAnalyzer.base import KeyValuePair


@attr.s(kw_only=True, slots=True)
class JavascriptAnalyzer:
    """JavascriptAnalyzer."""

    kvps: List[KeyValuePair] = attr.ib(factory=list)

    def analyze(self, content: str) -> None:
        """Analyze content.

        Args:

            content (str): Content to analyze.
        """

        from ContentAnalyzer.analyzers.javascript.parser import Visitor

        visitor = Visitor(text=content)

        try:
            tree = esprima.parse(content, delegate=visitor, options={'loc': True, 'tolerant': True})
            visitor.visit(tree)
            self.kvps = visitor.get_matches()
        except esprima.error_handler.Error:
            # esprima may have a hard time with sourcemaps so check if
            # the file's last line starts with 'sourcemap' and if so,
            # try parsing the file again without the last line
            parts = content.split('\n')
            if len(parts) > 1:
                if parts[-1].lower().startswith("sourcemap"):
                    new_content = "\n".join(parts[0:-1])
                    self.analyze(new_content)
                else:
                    # Last line doesn't start with 'sourcemap'
                    raise
            else:
                # Not more than 1 line in file
                raise


    def get_kvps(self) -> List[KeyValuePair]:
        """Get a list of KeyValuePairs.

        Returns:

            list: List of KeyValuePairs.
        """
        return self.kvps.copy()


# pylint: disable=line-too-long
# TEXT = """var client = twilio('ACc857fbb08e9355d3afcd09cea4e12acd', 'f8f9949838bffd7ab4d088e40eeb11bb');"""
TEXT = """module.exports = {
    tokenSecret: process.env.TOKEN_SECRET || 'A hard to guess string 555',
    providers: {
        'google': {
            clientId: process.env.GOOGLE_CLIENTID || '255148626257-q0vpd72frmemvfurnrbno2o1l28a2v3k.apps.googleusercontent.com',
            secret: process.env.GOOGLE_SECRET || 'VY6E0UQjg_OfOAsbFwgx8GRq'
        }
    }
};"""
# pylint: enable=line-too-long


# def main():
#     """Main."""

#     doc = JavascriptAnalyzer()
#     doc.analyze(TEXT)

#     print("", end='')

# if __name__ == "__main__":
#     main()
