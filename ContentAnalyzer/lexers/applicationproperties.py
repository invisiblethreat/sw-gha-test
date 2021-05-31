"""ApplicationPropertiesLexer Lexer."""

import re
import attr
from ContentAnalyzer.lexers import LexerMatchBase


@attr.s(kw_only=True, slots=True)
class ApplicationPropertiesKeyValue(LexerMatchBase):
    """ApplicationPropertiesKeyValue."""

    key = attr.ib(default=None, type=str)
    value = attr.ib(default=None, type=str)

    _field_match_mappings = attr.ib(default={
        1: 'comment',
        2: 'junk',
        3: 'junk',
        4: 'key',
        5: 'operator',
        6: 'value',
        11: 'value',
    })

    _token_index_mappings = attr.ib(default={
        'comment': 1,
        'junk': 2,
        'key': 3,
        'operator': 4,
        'value': 5,
    })

    _token_kind_mapping = attr.ib(default={
        'comment': ['analyzer', 'Comment'],
        'junk': ['analyzer', 'Junk'],
        'key': ['analyzer', 'Key'],
        'operator': ['analyzer', 'Operator'],
        'value': ['analyzer', 'Value'],
    })

    _token_kinds = attr.ib(default=[
        'analyzer.Comment',
        'analyzer.Junk',
        'analyzer.Key',
        'analyzer.Operator',
        'analyzer.Value',
    ])

    def consume_match(self, match):
        """Consume a regex match and populate self with it."""

        # TODO: Shouldn't need to implement this but have to for some reason
        if match.group(self._token_index_mappings['key']) is None:
            # Key value is None so return
            return

        if match.group(4) is not None:
            # key = match.group(4)
            match_number = 4
            field_name = "key"
            start_pos = match.start(match_number)
            kind = self._get_field_to_kind(field_name)
            value = match.group(match_number)

            match_tuple = self._make_token_tuple(start_pos, kind, value)

            setattr(self, field_name, match_tuple)
        else:
            raise RuntimeError("Couldn't find key!")
        if match.group(11) is not None:
            # Use this for value
            match_number = 11
            # start_pos = match.start(11)
            # kind = "value"
        elif match.group(8) is not None:
            # Use this for numeric values in quotes
            # e.g. "3600"
            match_number = 8
            # start_pos = match.start(8)
            # kind = "value"
        elif match.group(6) is not None:
            # Use as fall back value
            match_number = 6
            # start_pos = match.start(6)
            # kind = "value"
        else:
            raise RuntimeError("Don't know")

        field_name = "value"
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
class ApplicationPropertiesLexer():
    """ApplicationPropertiesLexer."""

    # pylint: disable=line-too-long
    # regex = attr.ib(default=r"^#? *((([a-zA-Z0-9\_\.\-]+)(=|: ))|#)(.*)\n?", type=str)
    # Won't catch 'export ' before value
    # regex = attr.ib(default=r"^#? {0,3}((([a-zA-Z0-9\_\.\-]+) *(=|:))|#) *(.*)\n?", type=str)
    # Catches 'export ' before value but match groups are now 3 and 6 and not 2 and 5
    # regex = attr.ib(default=r"^(#|export)? {0,3}((([a-zA-Z0-9\_\.\-]+) *(=|:))|#) *(.*)\n?", type=str)
    # Catch lots of shit. 4 is key. 6 is value... if 11 then value if 8 then value.
    regex = attr.ib(default=r"^(#|export)? {0,3}((([a-zA-Z0-9\_\.\-]+) *(=|:))|#) *((\"([0-9]+)\")|(\"\")|(\"([\w\W][^\"]+)\")|(.*))\n?", type=str)
    # pylint: enable=line-too-long

    def parse(self, text):
        """Parse text."""

        matches = re.finditer(self.regex, text, re.MULTILINE)

        entries = [ApplicationPropertiesKeyValue.from_regex_match(match) for match in matches]

        return entries

    def get_tokens_unprocessed(self, text):
        """Get tokens unprocessed."""

        entries = self.parse(text)
        for entry in entries:
            for prop in entry.tokens:
                yield prop

TEXT = """#
# Druid - a distributed column store.
# Copyright 2012 - 2015 Metamarkets Group Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# Extensions (no deep storage model is listed - using local fs for deep storage - not recommended for production)
# Also, for production to use mysql add, "io.druid.extensions:mysql-metadata-storage"
druid.extensions.loadList=["mysql-metadata-storage", "druid-kafka-eight", "druid-s3-extensions"]
druid.extensions.directory=extensions
druid.extensions.hadoopDependenciesDir=hadoopDependenciesDir

# Zookeeper
druid.zk.service.host=netsil-zookeeper.marathon.mesos:12181

# Metadata Storage (use something like mysql in production by uncommenting properties below)
# by default druid will use derby
druid.metadata.storage.type=mysql
druid.metadata.storage.connector.connectURI=jdbc:mysql://user-db.marathon.mesos:3306/druid
druid.metadata.storage.connector.user=druid
druid.metadata.storage.connector.password=diurd

# Deep storage (local filesystem for examples - don't use this in production)
druid.storage.type=local
druid.storage.storageDirectory=/tmp/druid/localStorage

# setup S3 deep storage
#druid.storage.type=s3
#druid.s3.accessKey=AKIAJRTI7WX3QDFFZCRA
#druid.s3.secretKey=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
#druid.storage.bucket=netsil-pro-druid-deep-storage
#druid.storage.baseKey=druid-segments

# Query Cache (we use a  10mb heap-based local cache on the broker)
druid.cache.type=local
druid.cache.sizeInBytes=10000000

# Coordinator Service Discovery
druid.selectors.coordinator.serviceName=druid-coordinator

# Indexing service discovery
druid.selectors.indexing.serviceName=druid-overlord

# Monitoring (disabled for examples)
# druid.monitoring.monitors=["com.metamx.metrics.SysMonitor","com.metamx.metrics.JvmMonitor"]

# Metrics logging (disabled for examples)
druid.emitter=logging
druid.emitter.logging.logLevel=debug"""

# pylint: disable=unused-variable
# def main():
#     """Main."""

#     lexer = ApplicationPropertiesLexer()
#     entries = list(lexer.get_tokens_unprocessed(TEXT))


#     print("breakpoint")

# if __name__ == "__main__":
#     main()
