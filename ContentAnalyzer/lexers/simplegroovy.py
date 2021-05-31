"""SimpleGroovy Lexer."""

import re
import attr
from ContentAnalyzer.lexers import LexerMatchBase

@attr.s(kw_only=True, slots=True)
class SimpleGroovyKeyValue(LexerMatchBase):
    """SimpleGroovyKeyValue."""

    key = attr.ib(default=None, type=str)
    value = attr.ib(default=None, type=str)

    _field_match_mappings = attr.ib(default={
        1: 'key',
        2: 'junk',
        3: 'value',
    })

    _token_index_mappings = attr.ib(default={
        'key': 1,
        'junk': 2,
        'value': 3,
    })

    _token_kind_mapping = attr.ib(default={
        'comment': ['analyzer', 'Comment'],
        'junk': ['analyzer', 'Junk'],
        'key': ['analyzer', 'Key'],
        'operator': ['analyzer', 'Operator'],
        'value': ['analyzer', 'Value'],
    })

    _token_kinds = attr.ib(default=[
        'analyzer.Key',
        'analyzer.Junk',
        'analyzer.Value',
        'analyzer.Operator',
        'analyzer.Comment',
    ])

    def consume_match(self, match):
        """Consume a regex match and populate self with it."""

        # TODO: Shouldn't need to implement this but have to for some reason
        if match.group(self._token_index_mappings['key']) is None:
            # Key value is None so return
            return

        if match.group(1) is not None:
            # key = match.group(4)
            match_number = 1
            field_name = "key"
            start_pos = match.start(match_number)
            kind = self._get_field_to_kind(field_name)
            value = match.group(match_number)

            match_tuple = self._make_token_tuple(start_pos, kind, value)

            setattr(self, field_name, match_tuple)
            match_number = 3
        else:
            raise RuntimeError("Couldn't find key!")
        # if match.group(7) is not None:
        #     # Use this for value
        #     match_number = 7
        # elif match.group(5) is not None:
        #     # Use this for numeric values in quotes
        #     # e.g. "3600"
        #     match_number = 5
        # else:
        #     raise RuntimeError("Don't know")

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
class SimpleGroovyLexer():
    """SimpleGroovyLexer."""

    # pylint: disable=line-too-long
    # 2 is key. 7 is value if in '' or 5 if in "".
    # STRING ASSIGNMENT
    # ^ *(\/\/|\*){0,1} *def ([\w\_\.\-]+) *= *(?:(\"([\w\W][^\"\n]+)\")|(?:\'([\w\W][^\'\n]+)\'))\n?
    # FUNCTION ARGUMENTS
    # ([\w]+)\((?:\"|\')([\w+_\-\.?!\"':\/@\\&;=<% \[\]*<>{}$]+)(?:\"|\')(?=(?:,\s+|\s+[a-zA-Z]|\)))
    # ([\w]+)\((?:(?:\"|\')([\w+_\-\.?!\"':\/@\\&;=<% \[\]*<>{}$]+)(?:\"|\')(,\s?(?:\"|\')([\w+_\-\.?!\"':\/@\\&;=<% \[\]*<>{}$]+)(?:\"|\'))?)+
    # STRING ASSIGNMENT VALUES AND FUNCTION ARGUMENTS (NON-KWARGS)
    # (?:@(?:[\w+])\()?(?:((?:([\w]+)\(|=))?(?:(?:\"|\')([\w+_\-\.?!\"':\/@\\&;=<% \[\]*<>{}$]+)(?:\"|\')(,\s((([\w]+)\(|=))(?:\"|\')([\w+_\-\.?!\"':\/@\\&;=<% \[\]*<>{}$]+)(?:\"|\'))?))+
    # (?:@([\w]+)\()?(?:(?:(?:([\w]+)(?:\(|=)))?(?:(?:\"|\')([\w+_\-\.?!\"':\/@\\&;=<% \[\]*<>{}$]+)(?:\"|\')(,\s(?:(?:([\w]+)(?:\(|=)))?(?:\"|\')([\w+_\-\.?!\"':\/@\\&;=<% \[\]*<>{}$]+)(?:\"|\'))*))
    # FUNCTION ARGUMENTS ONLY
    # (?:@([\w]+)\()?(?:(?:(?:([\w]+)(?:\(|=)))(?:(?:\"|\')([\w+_\-\.?!\"':\/@\\&;=<% \[\]*<>{}$]+)(?:\"|\')(,\s(?:(?:([\w]+)(?:\(|=)))?(?:\"|\')([\w+_\-\.?!\"':\/@\\&;=<% \[\]*<>{}$]+)(?:\"|\'))*))
    # FUNCTION ARGUMENTS ONLY (MISSES MULTIPLE NON-KWARGUMENTS TO FUNCTION LIKE ```session.prepare(insertInto("acs", "revisions")```)
    # (?:@([\w]+)\()?(?:(?:(?:([\w]+)(?:\(|=)))(?:(?:(?:\"|\')([\w+_\-\.?!\"':\/@\\&;=<% \[\]*<>{}$]+)(?:\"|\')(?:\)|,\s?)?)*(?:(?:(?:(?:([\w]+)(?:\(|=)))?(?:\"|\')([\w+_\-\.?!\"':\/@\\&;=<% \[\]*<>{}$]+)(?:\"|\')))))
    # FUNCTION ARGUMENTS ONLY (GETS KWARGS BUT ONLY GETS LAST LIST ARGUMENT)
    # regex = attr.ib(default=r"^ *(//|\*){0,1} *def ([a-zA-Z0-9\_\.\-]+) *= *((\"([\w\W][^\"\n]+)\")|(\'([\w\W][^\'\n]+)\'))\n?", type=str)
    # regex = attr.ib(default=r"^ *(\/\/|\*){0,1} *def ([\w\_\.\-]+) *= *(?:(\"([\w\W][^\"\n]+)\")|(?:\'([\w\W][^\'\n]+)\'))\n?")
    regex = attr.ib(default=r" *(?:\/\/|\*){0,1} *def ([\w\_\.\-]+) *= *(?:(?:\"([\w\W][^\"\n]+)\")|(?:\'([\w\W][^\'\n]+)\'))\n?")
    compiled_regex = attr.ib(default=None)
    # pylint: enable=line-too-long

    def __attrs_post_init__(self):

        self.compiled_regex = re.compile(self.regex, re.MULTILINE)

    def parse(self, text):
        """Parse text."""

        matches = re.finditer(self.compiled_regex, text)

        entries = [SimpleGroovyKeyValue.from_regex_match(match) for match in matches]

        return entries

    def get_tokens_unprocessed(self, text):
        """Get tokens unprocessed."""

        entries = self.parse(text)
        for entry in entries:
            for prop in entry.tokens:
                yield prop

TEXT = """import com.amazonaws.auth.BasicAWSCredentials
import com.amazonaws.internal.StaticCredentialsProvider
import com.amazonaws.services.s3.AmazonS3Client
import com.amazonaws.services.s3.model.GetObjectRequest
import com.datastax.driver.core.Cluster
import java.security.MessageDigest
import static com.datastax.driver.core.querybuilder.QueryBuilder.bindMarker
import static com.datastax.driver.core.querybuilder.QueryBuilder.insertInto
import static com.xlson.groovycsv.CsvParser.parseCsv
@Grab('com.xlson.groovycsv:groovycsv:1.1')
@Grab('com.datastax.cassandra:cassandra-driver-core:3.0.0-rc1')
@Grab(group='com.amazonaws', module='aws-java-sdk', version='1.10.27')
@groovy.lang.GrabExclude("commons-logging:commons-logging")
def clientId = 'AKIAIDMUIY2QZLABJ65Q'
def clientSecret = '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'
final String cassandra_address = args[0];
def bucketName = 'quickstream-data'
def cluster = Cluster.builder().addContactPoint(cassandra_address).build();
def session = cluster.connect()
def fileName = args[1]
def s3client = new AmazonS3Client(new StaticCredentialsProvider(new BasicAWSCredentials(clientId, clientSecret)))
def assetObjectRequest = new GetObjectRequest(bucketName, fileName);
def revisionObject = s3client.getObject(assetObjectRequest);
def revisionsData = parseCsv(new InputStreamReader(revisionObject.getObjectContent()))
def insertRevision = session.prepare(insertInto("acs", "revisions")
        .value("asset_id", bindMarker("asset_id"))
        .value("id", bindMarker("id"))
        .value("created", bindMarker("created"))
        .value("content_type", bindMarker("content_type"))
        .value("datalocation", bindMarker("datalocation"))
        .value("empty", bindMarker("empty")))
//.value("tags"))
for(line in revisionsData) {
    def boundStatement = insertRevision.bind()
            .setString("id", line.ID)
            .setString("asset_id", line.OBJ_ID)
            .setTimestamp("created", Date.parse("MMM dd yyyy H:m", line.OBJ_DATETIME))
            .setBool("empty", Boolean.parseBoolean(line.EMPTY))
            .setString("datalocation", MessageDigest.getInstance("MD5").digest(line.PATH.bytes).encodeHex().toString())
    session.executeAsync(boundStatement)
    println("inserted revision $line.ID")
session.close();
println("completed ");
System.exti(0);"""

# pylint: disable=unused-variable
# def main():
#     """Main."""

#     lexer = SimpleGroovyLexer()
#     entries = list(lexer.get_tokens_unprocessed(TEXT))


#     print("breakpoint")

# if __name__ == "__main__":
#     main()
