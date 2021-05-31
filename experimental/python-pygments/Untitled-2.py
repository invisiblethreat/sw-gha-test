
from pygments.lexers import PythonLexer
from pygments.lexers import JavaLexer


def read_contents(filename: str) -> str:
    """Read contents of file"""

    f = open(filename, 'r', encoding='utf-8')
    content = f.read()
    f.close()
    return content


def main():
    """Main."""

    # filename = "tests/data/python/sample1.py"
    # lexer_class = PythonLexer
    filename = "tests/data/java/sample1.java"
    lexer_class = JavaLexer

    content = read_contents(filename)
    lexer = lexer_class()
    tokens = [n for n in lexer.get_tokens_unprocessed(content)]


    print("", end='')

if __name__ == "__main__":
    main()
