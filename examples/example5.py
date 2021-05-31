"""Example 5"""

def main():
    """Main."""
    from ContentAnalyzer.lexers import Document

    blah = Document()
    blah.filename = "/home/terryrodery/arista/alab/bundle/src/constants/app.js"
    blah.set_lexer('javascript')

    blah.parse()

    for token in blah.get_tokens():
        print(token)

    print(blah.get_token_kinds())

    blah.newlines.get_line_for_pos(99999)

    print("breakpoint")

if __name__ == "__main__":
    main()
