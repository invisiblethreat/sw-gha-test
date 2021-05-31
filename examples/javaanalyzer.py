
from ContentAnalyzer.analyzers.java import JavaAnalyzer

CONTENT = """
package org.apache.lucene.spatial.prefix.tree;

import org.apache.lucene.spatial.prefix.tree.NumberRangePrefixTree;
import org.locationtech.spatial4j.shape.Shape;

public static interface NumberRangePrefixTree.NRShape extends Shape,
Cloneable {
    public String toString();

    public NumberRangePrefixTree.NRShape roundToLevel(int var1);
}
"""

def main():
    """main."""

    # filename = "./tests/data/python/sample15.py"

    # with open(filename, 'r', encoding='utf-8') as f:
    #     source = f.read()

    doc = JavaAnalyzer()
    doc.analyze(CONTENT)
    kvps = doc.get_kvps()

    print("breakpoint")

if __name__ == "__main__":
    main()
