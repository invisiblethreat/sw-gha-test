"""Sequentiality"""

import math
from typing import Optional, Union

from api_key_detector import charset as cset


# pylint: disable=unused-argument,line-too-long
def string_sequentiality(string: str, charset: str, plot_scatterplot: bool = False,
                         string_length: Optional[int] = None,
                         charset_length: Optional[Union[int, float]] = None) -> float:
    """
    Computes how much a string contains sequence of consecutive or distance-fixed characters

    :param string: the string
    :param charset: a charset as a string
    :param plot_scatterplot: optional boolean, if true plots a scatterplot

    :return: sequentiality index, 0 (low sequentiality) to 1 (high sequentiality)
    :rtype: float
    """

    if string_length is None:
        string_length = len(string)

    if string_length <= 2:
        return 0

    window_size = int(math.floor(math.log(string_length)))
    counter = 0
    buckets = {}
    for j in range(1, string_length):
        for i in range(max(j - window_size, 0), j):
            diff = math.fabs((ord(string[j]) - ord(string[i])))
            buckets[diff] = buckets.get(diff, 0) + 1
            counter += 1

    # normalize histogram
    for key in buckets:
        buckets[key] = buckets[key] / counter

    # Calculate MSE
    charset_buckets = cset.get_char_distance_distribution(charset, charset_length=int(charset_length))
    mse = 0.0
    number_of_keys = len(charset_buckets)
    for key in charset_buckets:
        diff = buckets.get(key, 0) - charset_buckets.get(key, 0)
        square_diff = diff ** 2
        mse += square_diff / number_of_keys

    return mse
# pylint: enable=unused-argument,line-too-long


def weighted_sequentiality(string: str, charset: str) -> float:
    """
    Returns the string sequentiality weighted by the string length. I.e.
    ABC is less meaningful than ABCDEFGHIJKLMNO

    :param string:
    :param charset:
    :return:
    """
    return string_sequentiality(string, charset) * len(string)


def main():
    """Main"""

    import sys

    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} string_to_be_computed")
        return

    narrower_charset = cset.get_narrower_charset(sys.argv[1])
    index = string_sequentiality(sys.argv[1], narrower_charset, plot_scatterplot=False)
    print(f"Sequentiality index: {index}")


if __name__ == '__main__':
    main()
