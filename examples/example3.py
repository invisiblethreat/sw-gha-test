
import re
import attr
from slimit.lexer import Lexer

def _read_file_contents(filename, binary=False):
    """Read the contents of a file."""

    if binary:
        f = open(filename, 'rb')
    else:
        f = open(filename, 'r', encoding='utf-8')

    data = f.read()
    f.close()
    return data

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
class JavaScriptLexer():
    """JavaScriptLexer"""

    filename = attr.ib(default=None, type=str)
    text = attr.ib(default=None, type=str)
    tokens = attr.ib(factory=dict)
    newlines = attr.ib(factory=NewLinePositions)
    lexer = attr.ib(factory=Lexer)

    def parse(self):
        """Parse"""
        if self.text is None and self.filename is not None:
            self.text = _read_file_contents(self.filename)

        self.lexer.input(self.text)
        for token in self.lexer:
            # if grab_next:
            if token.type not in self.tokens:
                self.tokens[token.type] = []

            # if token.type in ('ID', 'STRING', 'NUMBER'):
            #     self.tokens[token.type].append(token)
            self.tokens[token.type].append(token)

        self.__parse_newlines()

    def __parse_newlines(self):
        """Parse newlines."""

        self.newlines.parse(self.text)

    def get_tokens(self):
        for k, v in self.tokens.items():
            for token in v:
                value = token.value
                start_column = token.lexpos
                end_column = start_column + len(value)
                start_line = self.newlines.get_line_number(start_column)
                end_line = self.newlines.get_line_number(end_column)
                token_info = "%s %s %s %s %s %s" % (k, value, start_line, end_line, start_column, end_column)
                yield token_info

def main():
    """Main."""

    blah = JavaScriptLexer()
    blah.filename = "/home/terryrodery/arista/alab/bundle/src/constants/app.js"
    blah.parse()

    for token in blah.get_tokens():
        print(token)

if __name__ == "__main__":
    main()
