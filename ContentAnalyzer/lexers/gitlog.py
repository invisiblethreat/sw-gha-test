"""GitHead Lexer."""

import re
import attr
from ContentAnalyzer.lexers import LexerMatchBase

@attr.s(kw_only=True, slots=True)
class GitLogEntry(LexerMatchBase):
    """GitLogEntry."""

    prev_hash = attr.ib(default=None, type=str)
    commit_hash = attr.ib(default=None, type=str)
    user = attr.ib(default=None, type=str)
    email = attr.ib(default=None, type=str)
    timestamp = attr.ib(default=None, type=int)
    tz = attr.ib(default=None, type=int)
    action = attr.ib(default=None, type=str)
    message = attr.ib(default=None, type=str)

    _field_match_mappings = attr.ib(default={
        1: 'prev_hash',
        2: 'commit_hash',
        3: 'user',
        4: 'email',
        5: 'timestamp',
        6: 'tz',
        7: 'action',
        8: 'message',
    })

    _token_kind_mapping = attr.ib(default={
        'prev_hash': ['Commit', 'Hash'],
        'commit_hash': ['Commit', 'Hash'],
        'user': ['User', 'Name'],
        'email': ['User', 'Email'],
        'timestamp': ['Time', 'Timestamp'],
        'tz': ['Time', 'Timezone'],
        'action': ['Commit', 'Action'],
        'message': ['Commit', 'Message'],
    })

    _token_kinds = attr.ib(default=[
        'Commit.Hash',
        'User.Name',
        'User.Email',
        'Time.Timestamp',
        'Time.Timezone',
        'Commit.Action',
        'Commit.Message'
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
class GitLogLexer():
    """GitLogLexer."""

    # pylint: disable=line-too-long
    regex = attr.ib(default=r"([a-f0-9]{40}) ([a-f0-9]{40}) ([a-zA-Z0-9\_\- ]+) <(.*)> ([0-9]{0,10}) (\+[0-9]{4})\n([a-z]+): (.*)", type=str)
    # pylint: enable=line-too-long

    def parse(self, text):
        """Parse text."""

        matches = re.finditer(self.regex, text, re.MULTILINE)

        entries = [GitLogEntry.from_regex_match(match) for match in matches]

        return entries

    def get_tokens_unprocessed(self, text):
        """Get tokens unprocessed."""

        entries = self.parse(text)
        for entry in entries:
            for prop in entry.tokens:
                yield prop

TEXT = """
0000000000000000000000000000000000000000 808665c2ca8674a94cbb957ce072d0bd6bafe162 Ubuntu <ubuntu@box364.(none)> 1486337453 +0000
clone: from git@github.com:vrcadore/nutri-patients.git
808665c2ca8674a94cbb957ce072d0bd6bafe162 808665c2ca8674a94cbb957ce072d0bd6bafe162 Ubuntu <ubuntu@box364.(none)> 1486337453 +0000
reset: moving to 808665c2ca8674a94cbb957ce072d0bd6bafe162
808665c2ca8674a94cbb957ce072d0bd6bafe162 808665c2ca8674a94cbb957ce072d0bd6bafe162 Ubuntu <ubuntu@box364.(none)> 1486337453 +0000
branch: Reset to 808665c2ca8674a94cbb957ce072d0bd6bafe162
808665c2ca8674a94cbb957ce072d0bd6bafe162 808665c2ca8674a94cbb957ce072d0bd6bafe162 Ubuntu <ubuntu@box364.(none)> 1486337453 +0000
checkout: moving from dev to dev
808665c2ca8674a94cbb957ce072d0bd6bafe162 808665c2ca8674a94cbb957ce072d0bd6bafe162 Ubuntu <ubuntu@box364.(none)> 1486337453 +0000
reset: moving to 808665c2ca8674a94cbb957ce072d0bd6bafe162
808665c2ca8674a94cbb957ce072d0bd6bafe162 1ec64e0a5957a26640defd979014917dddddef29 Ubuntu <ubuntu@box3485.(none)> 1486338585 +0000
reset: moving to 1ec64e0a5957a26640defd979014917dddddef29
1ec64e0a5957a26640defd979014917dddddef29 1ec64e0a5957a26640defd979014917dddddef29 Ubuntu <ubuntu@box3485.(none)> 1486338585 +0000
branch: Reset to 1ec64e0a5957a26640defd979014917dddddef29
1ec64e0a5957a26640defd979014917dddddef29 1ec64e0a5957a26640defd979014917dddddef29 Ubuntu <ubuntu@box3485.(none)> 1486338585 +0000
checkout: moving from dev to dev
1ec64e0a5957a26640defd979014917dddddef29 1ec64e0a5957a26640defd979014917dddddef29 Ubuntu <ubuntu@box3485.(none)> 1486338585 +0000
reset: moving to 1ec64e0a5957a26640defd979014917dddddef29
1ec64e0a5957a26640defd979014917dddddef29 2443cd66b85a81830fcd93196d5e7c4efae05cea Ubuntu <ubuntu@box424.(none)> 1486339960 +0000
reset: moving to 2443cd66b85a81830fcd93196d5e7c4efae05cea
2443cd66b85a81830fcd93196d5e7c4efae05cea 2443cd66b85a81830fcd93196d5e7c4efae05cea Ubuntu <ubuntu@box424.(none)> 1486339960 +0000
branch: Reset to 2443cd66b85a81830fcd93196d5e7c4efae05cea
2443cd66b85a81830fcd93196d5e7c4efae05cea 2443cd66b85a81830fcd93196d5e7c4efae05cea Ubuntu <ubuntu@box424.(none)> 1486339960 +0000
checkout: moving from dev to dev
2443cd66b85a81830fcd93196d5e7c4efae05cea 2443cd66b85a81830fcd93196d5e7c4efae05cea Ubuntu <ubuntu@box424.(none)> 1486339960 +0000
reset: moving to 2443cd66b85a81830fcd93196d5e7c4efae05cea
2443cd66b85a81830fcd93196d5e7c4efae05cea 2443cd66b85a81830fcd93196d5e7c4efae05cea Ubuntu <ubuntu@box1268.(none)> 1486340477 +0000
reset: moving to 2443cd66b85a81830fcd93196d5e7c4efae05cea
2443cd66b85a81830fcd93196d5e7c4efae05cea 2443cd66b85a81830fcd93196d5e7c4efae05cea Ubuntu <ubuntu@box1268.(none)> 1486340477 +0000
branch: Reset to 2443cd66b85a81830fcd93196d5e7c4efae05cea
2443cd66b85a81830fcd93196d5e7c4efae05cea 2443cd66b85a81830fcd93196d5e7c4efae05cea Ubuntu <ubuntu@box1268.(none)> 1486340477 +0000
checkout: moving from dev to dev
2443cd66b85a81830fcd93196d5e7c4efae05cea 2443cd66b85a81830fcd93196d5e7c4efae05cea Ubuntu <ubuntu@box1268.(none)> 1486340477 +0000
reset: moving to 2443cd66b85a81830fcd93196d5e7c4efae05cea
2443cd66b85a81830fcd93196d5e7c4efae05cea 93017567d28362a1caf866691a9a045e12e3758d Ubuntu <ubuntu@box378.(none)> 1486342904 +0000
reset: moving to 93017567d28362a1caf866691a9a045e12e3758d
93017567d28362a1caf866691a9a045e12e3758d 93017567d28362a1caf866691a9a045e12e3758d Ubuntu <ubuntu@box378.(none)> 1486342904 +0000
branch: Reset to 93017567d28362a1caf866691a9a045e12e3758d
93017567d28362a1caf866691a9a045e12e3758d 93017567d28362a1caf866691a9a045e12e3758d Ubuntu <ubuntu@box378.(none)> 1486342904 +0000
checkout: moving from dev to dev
93017567d28362a1caf866691a9a045e12e3758d 93017567d28362a1caf866691a9a045e12e3758d Ubuntu <ubuntu@box378.(none)> 1486342904 +0000
reset: moving to 93017567d28362a1caf866691a9a045e12e3758d
93017567d28362a1caf866691a9a045e12e3758d 93017567d28362a1caf866691a9a045e12e3758d Ubuntu <ubuntu@box1628.(none)> 1486343236 +0000
reset: moving to 93017567d28362a1caf866691a9a045e12e3758d
93017567d28362a1caf866691a9a045e12e3758d 93017567d28362a1caf866691a9a045e12e3758d Ubuntu <ubuntu@box1628.(none)> 1486343236 +0000
branch: Reset to 93017567d28362a1caf866691a9a045e12e3758d
93017567d28362a1caf866691a9a045e12e3758d 93017567d28362a1caf866691a9a045e12e3758d Ubuntu <ubuntu@box1628.(none)> 1486343236 +0000
checkout: moving from dev to dev
93017567d28362a1caf866691a9a045e12e3758d 93017567d28362a1caf866691a9a045e12e3758d Ubuntu <ubuntu@box1628.(none)> 1486343236 +0000
reset: moving to 93017567d28362a1caf866691a9a045e12e3758d
93017567d28362a1caf866691a9a045e12e3758d 75cf16bac2ccf672174d09b50d9d70f571d4bb95 Ubuntu <ubuntu@box944.(none)> 1486343844 +0000
reset: moving to 75cf16bac2ccf672174d09b50d9d70f571d4bb95
75cf16bac2ccf672174d09b50d9d70f571d4bb95 75cf16bac2ccf672174d09b50d9d70f571d4bb95 Ubuntu <ubuntu@box944.(none)> 1486343844 +0000
branch: Reset to 75cf16bac2ccf672174d09b50d9d70f571d4bb95
75cf16bac2ccf672174d09b50d9d70f571d4bb95 75cf16bac2ccf672174d09b50d9d70f571d4bb95 Ubuntu <ubuntu@box944.(none)> 1486343844 +0000
checkout: moving from dev to dev
75cf16bac2ccf672174d09b50d9d70f571d4bb95 75cf16bac2ccf672174d09b50d9d70f571d4bb95 Ubuntu <ubuntu@box944.(none)> 1486343844 +0000
reset: moving to 75cf16bac2ccf672174d09b50d9d70f571d4bb95
75cf16bac2ccf672174d09b50d9d70f571d4bb95 69bea20516dee3ea1fe6ea23dfc2199b9c3297b0 Ubuntu <ubuntu@box820.(none)> 1486344490 +0000
reset: moving to 69bea20516dee3ea1fe6ea23dfc2199b9c3297b0
69bea20516dee3ea1fe6ea23dfc2199b9c3297b0 69bea20516dee3ea1fe6ea23dfc2199b9c3297b0 Ubuntu <ubuntu@box820.(none)> 1486344490 +0000
branch: Reset to 69bea20516dee3ea1fe6ea23dfc2199b9c3297b0
69bea20516dee3ea1fe6ea23dfc2199b9c3297b0 69bea20516dee3ea1fe6ea23dfc2199b9c3297b0 Ubuntu <ubuntu@box820.(none)> 1486344490 +0000
checkout: moving from dev to dev
69bea20516dee3ea1fe6ea23dfc2199b9c3297b0 69bea20516dee3ea1fe6ea23dfc2199b9c3297b0 Ubuntu <ubuntu@box820.(none)> 1486344490 +0000
reset: moving to 69bea20516dee3ea1fe6ea23dfc2199b9c3297b0
69bea20516dee3ea1fe6ea23dfc2199b9c3297b0 5c982900ceb8e7136092b2b72fc06243cafd22cb Ubuntu <ubuntu@box22.(none)> 1486650149 +0000
reset: moving to 5c982900ceb8e7136092b2b72fc06243cafd22cb
5c982900ceb8e7136092b2b72fc06243cafd22cb 5c982900ceb8e7136092b2b72fc06243cafd22cb Ubuntu <ubuntu@box22.(none)> 1486650149 +0000
branch: Reset to 5c982900ceb8e7136092b2b72fc06243cafd22cb
5c982900ceb8e7136092b2b72fc06243cafd22cb 5c982900ceb8e7136092b2b72fc06243cafd22cb Ubuntu <ubuntu@box22.(none)> 1486650149 +0000
checkout: moving from dev to dev
5c982900ceb8e7136092b2b72fc06243cafd22cb 5c982900ceb8e7136092b2b72fc06243cafd22cb Ubuntu <ubuntu@box22.(none)> 1486650149 +0000
reset: moving to 5c982900ceb8e7136092b2b72fc06243cafd22cb
5c982900ceb8e7136092b2b72fc06243cafd22cb a071b450099908206189c1a575da5247e1df4351 Ubuntu <ubuntu@box34.(none)> 1486650483 +0000
reset: moving to a071b450099908206189c1a575da5247e1df4351
a071b450099908206189c1a575da5247e1df4351 a071b450099908206189c1a575da5247e1df4351 Ubuntu <ubuntu@box34.(none)> 1486650483 +0000
branch: Reset to a071b450099908206189c1a575da5247e1df4351
a071b450099908206189c1a575da5247e1df4351 a071b450099908206189c1a575da5247e1df4351 Ubuntu <ubuntu@box34.(none)> 1486650483 +0000
checkout: moving from dev to dev
a071b450099908206189c1a575da5247e1df4351 a071b450099908206189c1a575da5247e1df4351 Ubuntu <ubuntu@box34.(none)> 1486650483 +0000
reset: moving to a071b450099908206189c1a575da5247e1df4351
a071b450099908206189c1a575da5247e1df4351 34a95c2497a269b23d5a97b383b6e227b6c8d352 Ubuntu <ubuntu@box11.(none)> 1486651573 +0000
reset: moving to 34a95c2497a269b23d5a97b383b6e227b6c8d352
34a95c2497a269b23d5a97b383b6e227b6c8d352 34a95c2497a269b23d5a97b383b6e227b6c8d352 Ubuntu <ubuntu@box11.(none)> 1486651573 +0000
branch: Reset to 34a95c2497a269b23d5a97b383b6e227b6c8d352
34a95c2497a269b23d5a97b383b6e227b6c8d352 34a95c2497a269b23d5a97b383b6e227b6c8d352 Ubuntu <ubuntu@box11.(none)> 1486651573 +0000
checkout: moving from dev to dev
34a95c2497a269b23d5a97b383b6e227b6c8d352 34a95c2497a269b23d5a97b383b6e227b6c8d352 Ubuntu <ubuntu@box11.(none)> 1486651573 +0000
reset: moving to 34a95c2497a269b23d5a97b383b6e227b6c8d352
34a95c2497a269b23d5a97b383b6e227b6c8d352 ef8d0b2aaaa1776fe11eca737e9de1f69fe19b64 Ubuntu <ubuntu@box136.(none)> 1486654566 +0000
reset: moving to ef8d0b2aaaa1776fe11eca737e9de1f69fe19b64
ef8d0b2aaaa1776fe11eca737e9de1f69fe19b64 ef8d0b2aaaa1776fe11eca737e9de1f69fe19b64 Ubuntu <ubuntu@box136.(none)> 1486654566 +0000
branch: Reset to ef8d0b2aaaa1776fe11eca737e9de1f69fe19b64
ef8d0b2aaaa1776fe11eca737e9de1f69fe19b64 ef8d0b2aaaa1776fe11eca737e9de1f69fe19b64 Ubuntu <ubuntu@box136.(none)> 1486654566 +0000
checkout: moving from dev to dev
ef8d0b2aaaa1776fe11eca737e9de1f69fe19b64 ef8d0b2aaaa1776fe11eca737e9de1f69fe19b64 Ubuntu <ubuntu@box136.(none)> 1486654566 +0000
reset: moving to ef8d0b2aaaa1776fe11eca737e9de1f69fe19b64
"""

# def main():
#     """Main."""

#     gh = GitLogLexer()
#     entries = list(gh.get_tokens_unprocessed(TEXT))

#     print("breakpoint")

# if __name__ == "__main__":
#     main()
