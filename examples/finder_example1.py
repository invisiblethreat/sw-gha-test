"""Finder example"""

import attr
from ContentAnalyzer.analyzers import JsonAnalyzer
from ContentAnalyzer.finder import Finder

@attr.s(kw_only=True, slots=True)
class ExampleFile:
    """ExampleFile."""

    name = attr.ib(type=str)
    content = attr.ib(type=str)

def read_all_file_data(filename):
    """Read all file data"""

    with open(filename, "r", encoding='utf-8') as f:
        data = f.read()
        return data

def main():
    """Main."""

    doc = JsonAnalyzer()
    doc.filename = "/home/terryrodery/arista/alab/bundle/package.json"
    doc.analyze(cheap=True)

    file_ = ExampleFile(name=doc.filename, content=read_all_file_data(doc.filename))

    finder = Finder(file_=file_)
    finder.find()

    print("breakpoint")

if __name__ == "__main__":
    main()
