"""Docker Compose analyzer."""

from ContentAnalyzer.lexers import Document, KeyValuePair

class DockerComposeAnalyzer(Document):
    """DockerComposeAnalyzer"""

    # pylint: disable=unused-argument
    def analyze(self, content):
        """Analyze content.

        Args:
            content (str): Content to analyze.
        """

        self.set_lexer("DockerComposeLexer")

        self.parse(content)

        left_side = None
        right_side = None
        for token in self.all_tokens:
            if token.kind == "analyzer.Key":
                left_side = token
            elif token.kind == "analyzer.Value":
                right_side = token
                kv_pair = KeyValuePair.from_tokens(left_side, right_side)
                self.kvps.append(kv_pair)
                left_side = None
                right_side = None
            else:
                raise ValueError("Unknown token kind '%s'" % token.kind)

    # pylint: enable=unused-argument

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

# def main():
#     """Main."""

#     doc = DockerComposeAnalyzer()
#     doc.analyze(content=TEXT)

#     # kinds = doc.get_token_kinds()
#     # print("expected = [")
#     # for n in kinds:
#     #     print("    '%s'," % n)
#     # print("]")

#     # print("expected = {")
#     # for kind in kinds:
#     #     print("    '%s': %s," % (kind, len(list(doc.get_tokens(kind=kind)))))
#     # print("}")

#     # for n in doc.get_kvps(as_kvp=True):
#     #     print(n)

#     print("breakpoint")

# if __name__ == "__main__":
#     main()
