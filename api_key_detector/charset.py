"""Charset"""

import math
from functools import lru_cache
from typing import Dict, List, Optional, Tuple, Union

# pylint: disable=line-too-long
CHARSETS = {
    # characters order is important, should follow the ascii table index
    "HEX_CHARS": "0123456789ABCDEFabcdef",
    "HEX_CHARS_EXT": "-0123456789ABCDEFabcdef",  # for GUID
    "BASE64_CHARS": "+/0123456789=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
    "BASE64_CHARS_EXT": "+-/0123456789=ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz",
    "BASE64_CHARS_EXT2": "+,-./0123456789;=ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz",
    "BASE91_CHARS": "!\"#$%&()*+,./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~",
    "BASE91_CHARS_EXT": "!\"#$%&()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~",
    "PRINT_CHARS": " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~",
}
# pylint: enable=line-too-long

CHARSETS_FLOAT_LENGTH = {
    "HEX_CHARS": 22.0,
    "HEX_CHARS_EXT": 23.0,
    "BASE64_CHARS": 65.0,
    "BASE64_CHARS_EXT": 67.0,
    "BASE64_CHARS_EXT2": 70.0,
    "BASE91_CHARS": 92.0,
    "BASE91_CHARS_EXT": 93.0,
    "PRINT_CHARS": 95.0,
}

# pylint: disable=line-too-long
def get_narrower_charset(string: str) -> Tuple[Union[str, None], Union[float, None]]:
    """
    Return the narrowest charset (among those defined) for the submitted string

    :param string: the string of which should be find the charset
    :return: the narrowest charset
    :rtype: str
    """
    for name, charset in CHARSETS.items():
        charset_found = True
        for c in set(string):
            if c not in charset:
                charset_found = False
                break

        if charset_found:
            return charset, CHARSETS_FLOAT_LENGTH[name]

    return None, None
# pylint: enable=line-too-long

@lru_cache(maxsize=65536)
def get_charset_intervals(charset: str) -> List[Tuple[int, int]]:
    """
    Given a charset, returns a list of INCLUSIVE (i.e. [a,b] in mathematical noation)
    intervals relative to the ascii table.
    For example, inserting 0123456789ABCDEFabcdef, the returned list will be
    [(48, 57), (65, 70), (97, 102)]

    :param charset: the charset as a string
    :return: a list of intervals
    :rtype: list
    """

    charset_set_list = sorted(set(charset), key=lambda char: ord(char)) # pylint: disable=unnecessary-lambda

    if len(charset_set_list) < 1:
        return None

    if len(charset_set_list) == 1:
        return [ord(charset[0])]

    left_index = ord(charset_set_list[0])
    latest_index = left_index
    intervals = []
    for c in charset_set_list[1:]:
        ord_c = ord(c)
        if ord_c != (latest_index + 1):
            intervals.append((left_index, latest_index))
            left_index = ord_c
        latest_index = ord_c

    intervals.append((left_index, latest_index))
    return intervals


@lru_cache(maxsize=262144)
def get_char_distance_distribution(charset: str, charset_length: Optional[int] = None) -> Dict:
    """
    Calculates the distribution of the distance between characters.
    VERY slow, to be used with @Memoized
    for good performance (if only a predetermined set of charsets is needed)

    :param charset: the charset as a string
    :return: a (normalized) histogram with the distribution of distance
    :rtype: dict
    """

    if charset_length is None:
        charset_length = len(charset)

    if charset_length <= 1:
        return {0: 1}

    buckets = {}
    counter = 0
    for i, _ in enumerate(charset):
        for j, _ in enumerate(charset):
            index = int(math.fabs(ord(charset[i]) - ord(charset[j])))
            buckets[index] = buckets.get(index, 0) + 1
            counter += 1

    # normalize histogram
    for key in buckets:
        buckets[key] = buckets[key] / counter

    return buckets


def main():
    """Main"""

    import sys

    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} charset_string")
        return

    print(str(get_char_distance_distribution(sys.argv[1])))


if __name__ == '__main__':
    main()
