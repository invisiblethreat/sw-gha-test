"""Example PHP Antlr4 parser"""

from ContentAnalyzer.analyzers.php import PhpAnalyzer

def main():
    """Main."""

    filename = "tests/data/php/sample1.php"

    anal = PhpAnalyzer.from_file(filename)

    for kvp in anal.get_kvps():
        print(kvp)
        print(kvp.to_dict())

    print("", end='')

if __name__ == "__main__":
    main()
