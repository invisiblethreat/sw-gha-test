def lex_stream_and_walk_tree_listener(filename: str):
    """Run lexer and parser on a filename.

    Creates InputStream, PathGrammarLexer, PathGrammarParser,
    ExtendedPathGrammarListener, and runs ParseTreeWalker.

    Args:
        filename (str): Filename to lex and parse.

    Returns:

        ExtendedPathGrammarListener: Path listener.
    """

    import antlr4
    from antlr4.tree.Tree import TerminalNodeImpl
    from experimental.php.PhpLexer import PhpLexer
    from experimental.php.PhpBaseLexer import PhpBaseLexer
    # from PathGrammarListener import PathGrammarListener
    from experimental.php.PhpParserListener import PhpParserListener

    from experimental.php.ExtendedPhpParserListener import ExtendedPhpParserListener
    from experimental.php.PhpParserVisitor import PhpParserVisitor
    from experimental.php.PhpParser import PhpParser

    if len(filename.split('\n')) == 1:
        with open(filename, 'r', encoding='utf-8') as f:
            data = f.read()
    else:
        data = filename
    stream = antlr4.InputStream(data)

    lexer = PhpLexer(stream)

    stream = antlr4.CommonTokenStream(lexer)
    parser = PhpParser(stream)
    tree = parser.htmlDocument()


    printer = ExtendedPhpParserListener()

    walker = antlr4.ParseTreeWalker()
    walker.walk(printer, tree)
    # visitor = PhpParserVisitor()
    # res = visitor.visit(tree)
    # print("", end='')
    # return printer
    # return tree

def main():
    """Main."""

    filename = "experimental/php/samples/db.php"
    printer = lex_stream_and_walk_tree_listener(filename)

    print("", end='')

if __name__ == "__main__":
    main()
