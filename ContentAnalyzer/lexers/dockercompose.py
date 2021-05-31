"""Docker Compose Lexer."""

import re
import attr
from ContentAnalyzer.lexers import LexerMatchBase

@attr.s(kw_only=True, slots=True)
class DockerComposeKeyValue(LexerMatchBase):
    """DockerComposeKeyValue."""

    key = attr.ib(default=None, type=str)
    value = attr.ib(default=None, type=str)

    _field_match_mappings = attr.ib(default={
        1: 'key',
        2: 'value',
    })

    _token_kind_mapping = attr.ib(default={
        'key': ['analyzer', 'Key'],
        'value': ['analyzer', 'Value'],
    })

    _token_kinds = attr.ib(default=[
        'analyzer.Key',
        'analyzer.Value',
    ])

    def consume_match(self, match):
        """Consume a regex match and populate self with it."""

        for match_number, field_name in self._field_match_mappings.items():
            start_pos = match.start(match_number)
            kind = self._get_field_to_kind(field_name)
            value = match.group(match_number)

            match_tuple = self._make_token_tuple(start_pos, kind, value)

            setattr(self, field_name, match_tuple)

    # pylint: disable=no-member
    @property
    def tokens(self):
        """Spits out tokens from attributes."""

        props = [n for n in self.__slots__ if not n.startswith('_') and n != "__weakref__"]

        for n in props:
            token = getattr(self, n)
            yield token
    # pylint: enable=no-member

    @classmethod
    def from_dict(cls, data):
        """Instantiate class from a dict."""

        instance = cls()
        for k, v in data.items():
            try:
                setattr(instance, k, v)
            except AttributeError:
                # We don't have this attribute so ignore
                pass

        return instance

    @classmethod
    def from_regex_match(cls, match):
        """Instantiate class from a regex match."""

        instance = cls()
        instance.consume_match(match)

        return instance

@attr.s(kw_only=True, slots=True)
class DockerComposeLexer():
    """DockerComposeLexer."""

    # pylint: disable=line-too-long
    regex = attr.ib(default=r"^\s+\- ([a-zA-Z0-9_\-\.]+)=([a-zA-Z0-9_\-\.\?\!\"\'\:\/\\\@\;\=\{\}\$]+)", type=str)
    # pylint: enable=line-too-long

    def parse(self, text):
        """Parse text."""

        matches = re.finditer(self.regex, text, re.MULTILINE)

        entries = [DockerComposeKeyValue.from_regex_match(match) for match in matches]

        return entries

    def get_tokens_unprocessed(self, text):
        """Get tokens unprocessed."""

        entries = self.parse(text)
        for entry in entries:
            for prop in entry.tokens:
                yield prop

TEXT = """version: '2'
services:
  myhero-ernst:
    build: .
    image: juliocisco/myhero-ernst
    ports:
     - "15000:5000"
    environment:
     - myhero_data_key=${MYHERO_DATA_KEY}
     - myhero_data_server=http://myhero-data:5000
     - myhero_mqtt_host=myhero-mosca
     - myhero_mqtt_port=1883
     - myhero_data_server=http://myhero-data:5000
networks:
  default:
     external:
       name: myherodata_default
"""

# # pylint: disable=unused-variable
# def main():
#     """Main."""

#     lexer = DockerComposeLexer()
#     entries = list(lexer.get_tokens_unprocessed(TEXT))

#     print("breakpoint")

# if __name__ == "__main__":
#     main()
