
from ContentAnalyzer.analyzers.python import PythonAnalyzer

def main():
    """main."""

    filename = "./tests/data/python/sample15.py"

    with open(filename, 'r', encoding='utf-8') as f:
        source = f.read()

    doc = PythonAnalyzer()
    doc.analyze(source)

    print("breakpoint")

if __name__ == "__main__":
    main()
