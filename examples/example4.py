import attr
import re
import pygments

KEEP_TOKENS = [
    'Name.Other',
    'Literal.String.Single',
    'Literal.String.Backtick',
    'Comment.Single',
    'Comment.Multiline',
]

def _read_file_contents(filename, binary=False):
    """Read the contents of a file."""

    if binary:
        f = open(filename, 'rb')
    else:
        f = open(filename, 'r', encoding='utf-8')

    data = f.read()
    f.close()
    return data

@attr.s(kw_only=True, slots=True, frozen=True)
class LexerToken():
    """LexerToken."""

    pos = attr.ib(default=None, type=int)
    length = attr.ib(default=None, type=int)
    kind = attr.ib(default=None, type=str)
    value = attr.ib(default=None)

    @property
    def stripped_value(self):
        """Returns 'value' but stripped."""
        return self.value.strip()

    @classmethod
    def from_lexer(cls, data):
        """Instantiate class from an unprocessed lexer token."""
        kwargs = {
            'pos': data[0],
            'length': len(data[2]),
            'kind': ".".join(data[1]),
            'value': data[2]
        }
        token = cls(**kwargs)
        return token

@attr.s(kw_only=True, slots=True)
class NewLinePositions():
    """NewLinePositions"""

    newlines = attr.ib(factory=list)

    def parse(self, data):
        """Calculate new line positions"""

        matches = re.finditer(r"\n", data, re.MULTILINE)

        for match_number, match in enumerate(matches, start=1):

            add_new_line = {
                'number': match_number,
                'pos': match.start()
            }
            self.newlines.append(add_new_line)

    def __calculate_column(self, line_number, pos):
        newline = self.newlines[line_number - 1]
        return pos - newline['pos'] - 1

    def get_line_number(self, pos):
        """Calculate the line number for a position"""

        highest_pos = 0
        newline_number = 0

        for line in self.newlines:
            if pos > line['pos']:
                # Given position is higher than this new line's position which is good
                highest_pos = line['pos']
                newline_number = line['number']

            if pos < line['pos']:
                # Given position is less than this line's so our line number is going
                # to be the last line number we iterated over
                break

        return newline_number

@attr.s(kw_only=True, slots=True)
class Document():
    """Document."""

    filename = attr.ib(default=None, type=str)
    text = attr.ib(default=None, type=str)
    tokens = attr.ib(factory=dict)
    newlines = attr.ib(factory=NewLinePositions)
    lexer = attr.ib(default=None)

    def parse(self):
        """Parse"""
        if self.text is None and self.filename is not None:
            self.text = _read_file_contents(self.filename)

        for unprocessed_token in self.lexer.get_tokens_unprocessed(self.text):
            token = LexerToken.from_lexer(unprocessed_token)
            if token.kind not in self.tokens:
                self.tokens[token.kind] = []

            self.tokens[token.kind].append(token)

        self.__parse_newlines()

    def set_lexer(self, name):
        self.lexer = pygments.lexers.get_lexer_by_name(name)

    def __parse_newlines(self):
        """Parse newlines."""

        self.newlines.parse(self.text)

    def get_tokens(self):
        for k, v in self.tokens.items():
            for token in v:
                value = token.value
                start_column = token.pos
                end_column = start_column + len(value)
                start_line = self.newlines.get_line_number(start_column)
                end_line = self.newlines.get_line_number(end_column)
                token_info = "%s %s %s %s %s %s" % (k, value, start_line, end_line, start_column, end_column)
                yield token_info

def main():
    """Main."""

    from pygments.lexers.javascript import JavascriptLexer

    blah = Document()
    blah.filename = "/home/terryrodery/arista/alab/bundle/src/constants/app.js"
    blah.set_lexer('javascript')

    blah.parse()

    # lexer = JavascriptLexer()

    # lexer_tokens = lexer.get_tokens_unprocessed(data)

    # KEEP_TOKENS = [
    #     'Name.Other',
    #     'Literal.String.Single',
    #     'Literal.String.Backtick',
    #     'Comment.Single',
    #     'Comment.Multiline',
    # ]

    # for token in lexer_tokens:
    #     new_token = LexerToken.from_lexer(token)
    #     if new_token.kind in KEEP_TOKENS:
    #         print(new_token)

    print("breakpoint")

if __name__ == "__main__":
    main()
