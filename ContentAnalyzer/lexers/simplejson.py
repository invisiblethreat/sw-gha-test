"""Simple Json Lexer."""

import re
import attr
from ContentAnalyzer.lexers import LexerMatchBase

@attr.s(kw_only=True, slots=True)
class SimpleJsonKeyValue(LexerMatchBase):
    """SimpleJsonKeyValue."""

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

        # For this lexer the key is going to be group 1 and the value
        # will be group 3 UNLESS value is a bool or int in which case
        # the value will be group 2. Otherwise, group 2 will contain
        # the string enclosed in quotes.
        value = match.group(3)
        if value is None:
            # Must be a bool or int
            value_match_group = 2
        else:
            value_match_group = 3
        start_pos = match.start(value_match_group)
        kind = self._get_field_to_kind('value')
        value = match.group(value_match_group)
        match_tuple = self._make_token_tuple(start_pos, kind, value)
        setattr(self, 'value', match_tuple)

        # Now handle key group
        start_pos = match.start(1)
        kind = self._get_field_to_kind('key')
        value = match.group(1)
        match_tuple = self._make_token_tuple(start_pos, kind, value)
        setattr(self, 'key', match_tuple)


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
class SimpleJsonLexer():
    """SimpleJsonLexer."""

    # pylint: disable=line-too-long
    # regex = attr.ib(default=r"^\s+\"([a-zA-Z0-9_\-\.]+)\":\s+(\"([\S ]*)\"|true|false|null|[0-9]+)", type=str)
    regex = attr.ib(default=r"^(?:(?:\s*(?:\/\/)?)\s*)\"([\w_\-\.]+)\":\s+((?:\"([\S ]*)\"|true|false|null|[0-9]+))")
    compiled_regex = attr.ib(default=None)
    # pylint: enable=line-too-long

    def __attrs_post_init__(self):

        self.compiled_regex = re.compile(self.regex, re.MULTILINE)

    def parse(self, text):
        """Parse text."""

        matches = re.finditer(self.compiled_regex, text)

        entries = [SimpleJsonKeyValue.from_regex_match(match) for match in matches]

        return entries

    def get_tokens_unprocessed(self, text):
        """Get tokens unprocessed."""

        entries = self.parse(text)
        for entry in entries:
            for prop in entry.tokens:
                yield prop

TEXT = """{
    "name": "amex-ap",
    "version": "0.1.0",
    "private": true,
    "dependencies": {
        "material-ui": "next",
        "material-ui-icons": "^1.0.0-beta.17",
        "react": "^15.6.1",
        "react-dom": "^15.6.1",
        "react-scripts": "^1.0.11",
        "react-tap-event-plugin": "^2.0.1",
        "typeface-roboto": "0.0.35"
    },
    "optionalDependencies": {
        "fsevents": "*"
    },
    "devDependencies": {
        "babel-core": "^6.2.1",
        "babel-loader": "^6.2.0",
        "babel-preset-es2015": "^6.1.18",
        "babel-preset-react": "^6.1.18",
        "html-webpack-plugin": "^2.30.1",
        "webpack": "^1.12.9",
        "webpack-dev-server": "^1.14.0"
    },
    "scripts": {
        "start": "react-scripts start",
        "build": "react-scripts build",
        "test": "react-scripts test --env=jsdom",
        "eject": "react-scripts eject"
    }
}
"_from": "agentkeepalive@^3.3.0",
  "_id": "agentkeepalive@3.3.0",
  "_inBundle": false,
  "_integrity": "sha512-9yhcpXti2ZQE7bxuCsjjWNIZoQOd9sZ1ZBovHG0YeCRohFv73SLvcm73PC9T3olM4GyozaQb+4MGdQpcD8m7NQ==",
  "_location": "/npm-profile/make-fetch-happen/agentkeepalive",
  "_phantomChildren": {},
  "_requested": {
    "type": "range",
    "registry": true,
    "raw": "agentkeepalive@^3.3.0",
    "name": "agentkeepalive",
    "escapedName": "agentkeepalive",
    "rawSpec": "^3.3.0",
    "saveSpec": null,
    "fetchSpec": "^3.3.0"
  },
  "_requiredBy": [
    "/npm-profile/make-fetch-happen"
  ],
  "_resolved": "https://registry.npmjs.org/agentkeepalive/-/agentkeepalive-3.3.0.tgz",
  "_shasum": "6d5de5829afd3be2712201a39275fd11c651857c",
  "_spec": "agentkeepalive@^3.3.0",
  "_where": "/Users/rebecca/code/npm/node_modules/npm-profile/node_modules/make-fetch-happen",
  "author": {
    "name": "fengmk2",
    "email": "fengmk2@gmail.com",
    "url": "https://fengmk2.com"
  },
  "browser": "browser.js",
  "bugs": {
    "url": "https://github.com/node-modules/agentkeepalive/issues"
  },
  "bundleDependencies": false,
  "ci": {
    "version": "4.3.2, 4, 6, 7, 8"
  },
  "dependencies": {
    "humanize-ms": "^1.2.1"
  },
  "deprecated": false,
  "description": "Missing keepalive http.Agent",
  "devDependencies": {
    "autod": "^2.8.0",
    "egg-bin": "^1.10.3",
    "egg-ci": "^1.7.0",
    "eslint": "^3.19.0",
    "eslint-config-egg": "^4.2.0",
    "pedding": "^1.1.0"
  },
  "engines": {
    "node": ">= 4.0.0"
  },
  "files": [
    "index.js",
    "browser.js",
    "lib"
  ],
  "homepage": "https://github.com/node-modules/agentkeepalive#readme",
  "keywords": [
    "http",
    "https",
    "agent",
    "keepalive",
    "agentkeepalive"
  ],
  "license": "MIT",
  "main": "index.js",
  "name": "agentkeepalive",
  "repository": {
    "type": "git",
    "url": "git://github.com/node-modules/agentkeepalive.git"
  },
  "scripts": {
    "autod": "autod",
    "ci": "npm run lint && npm run cov",
    "cov": "egg-bin cov",
    "lint": "eslint lib test index.js",
    "test": "egg-bin test"
  },
  "version": "3.3.0"
"""

# pylint: disable=unused-variable
# def main():
#     """Main."""

#     lexer = SimpleJsonLexer()
#     entries = list(lexer.get_tokens_unprocessed(TEXT))

#     print("breakpoint")

# if __name__ == "__main__":
#     main()
