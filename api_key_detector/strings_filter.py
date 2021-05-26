"""StringsFilter"""

from typing import List, Set
from api_key_detector.words_finder_singleton import finder


def _load_blacklists(files: List[str]) -> Set[str]:
    """Load blacklists from a list of filenames.

    Args:

        files (List[str]): List of paths containing blacklisted words.

    Returns:

        Set[str]: Set containing blacklisted words.
    """

    blacklist = set()
    for filename in files:
        for line in open(filename, "r", encoding='utf-8'):
            blacklist.add(line.replace('\n', '').replace('\r', ''))

    return blacklist


class StringsFilter:
    """StringsFilter.

    Args:

        min_key_length (int): Minimum key length.
        max_key_length (int): Maximum key length.
        word_content_threshold?
        blacklists (List[str], optional): List of paths containing blacklisted words.

    """

    # pylint: disable=line-too-long
    def __init__(self, min_key_length: int, max_key_length: int, word_content_threshold, blacklists: List[str] = None):
        self.min_key_length = min_key_length
        self.max_key_length = max_key_length
        self.word_content_threshold = word_content_threshold
        self.blacklist = set()

        if blacklists is not None:
            self.blacklist = _load_blacklists(blacklists)
    # pylint: enable=line-too-long


    def pre_filter(self, string: str) -> bool:
        """Perform pre-filtering of strings.

        True for ok, False for not ok.

        Args:

            string (str): String to check.

        Returns:

            bool: Whether or not string is filtered (and therefore invalid).
         """

        # Filter empty strings, or those less than or
        # greater than mix/max length
        if not string or len(string) < self.min_key_length or len(string) > self.max_key_length:
            return False

        # Check blacklist
        if self.blacklist and string in self.blacklist:
            return False

        # Filter strings that are hex numbers
        if string.startswith(('0x', '0X', '-0x', '-0X')):
            if string.endswith('L'):
                s = string[:-1]
            else:
                s = string
            try:
                int(s, 16)
                return False
            except ValueError:
                pass

        # String not filtered
        return True


    def pre_filter_mystring(self, mystring) -> bool:
        """
        MyString version of pre_filter

        :param mystring: the string that should be evaluated
        :type mystring: MyString
        :return: False if it can't be an API key, True otherwise
        """
        if not mystring:
            return False
        else:
            return self.pre_filter(mystring.value)


    def post_filter(self, string: str) -> bool:
        """Post filter"""
        if finder.get_words_percentage(string) >= self.word_content_threshold:
            return False
        return True


    def post_filter_mystring(self, mystring) -> bool:
        """Post filter mystring"""
        if not mystring:
            return False
        else:
            return self.post_filter(mystring.value)
