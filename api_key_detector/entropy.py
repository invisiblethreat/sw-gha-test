"""Entropy"""

from typing import Optional
import math


def shannon_entropy(item: str, itemset: str, item_length: Optional[int] = None) -> float:
    """Calculate shannon entropy for a value using a given character set.

    Calculates entropy based upon characters present in a
    set rather than just the characters present in the string itself.

    Args:

        item (str): Value to calculate entropy for.
        itemset (str): Character set to use for calculation.

    Returns:

        float: Entropy value.
    """

    if not item:
        return 0

    if item_length is None:
        item_length = len(item)

    entropy = 0.0
    for x in itemset:
        p_x = float(item.count(x)) / item_length
        if p_x > 0:
            entropy = entropy + (p_x * math.log(p_x, 2))

    return -entropy


# pylint: disable=line-too-long
def normalized_entropy(item: set, itemset: str, charset_normalization: bool = False, item_length: Optional[int] = None) -> float:
    """
    Calculates the [String] Shannon Entropy relative to the specific item length and set [charset]
    (i.e. weighted by the itemset's [charset's] complexity), if charset_normalization is True

    :param item: the item [string] of which should be computed the entropy
    :param itemset: an iterable representing the item set [charset as a string]
    :param charset_normalization: if True, normalize entropy with respect to the item length AND length of the charset
    :return: normalized entropy
    :rtype: float
    """

    if item_length is None:
        item_length = len(item)

    if charset_normalization:
        return shannon_entropy(item, itemset, item_length=item_length) / (item_length * len(itemset))
    return shannon_entropy(item, itemset, item_length=item_length) / item_length
# pylint: enable=line-too-long

def main():
    """Main"""

    import sys

    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} \"string to be classified\" charset")
        return

    print(shannon_entropy(sys.argv[1], sys.argv[2]))


if __name__ == '__main__':
    main()
