
from ContentAnalyzer.context import AnalyzerFileContext

def main():
    """Main."""

    full_path = "usr/lib/node_modules/sprintf-js/src/angular-sprintf.js"

    doc = AnalyzerFileContext.from_full_path(full_path)

    print("breakpoint")

if __name__ == "__main__":
    main()
