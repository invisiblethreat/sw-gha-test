"""Detector"""

from functools import lru_cache
from typing import List

from api_key_detector.string_classifier_singleton import classifier
from api_key_detector.strings_filter_singleton import s_filter


@lru_cache(maxsize=16384)
def __string_pipeline(string: str, classification_threshold: float = 0.5) -> bool:
    """Perform pre-filter, classification, post-filtering of string.

    Args:

        strings (List[str]): List of strings to detect.
        classification_threshold (float): Threshold for api key. Defaults to 0.5.

    Returns:

        bool: Whether or not string is an api key.
    """

    status = False
    if s_filter.pre_filter(string):
        classification = classifier.predict_strings([string])
        if classification > classification_threshold:
            if s_filter.post_filter(string):
                status = True

    return status


def filter_api_keys(strings: List[str]) -> List[str]:
    """Filter api keys.

    Apply pre and post filtering of strings and return a list
    of strings there were detected as api key.

    Args:

        strings (List[str]): List of strings to detect.

    Returns:

        List[str]: List containing strings that are classified as api.
    """

    # List comprehension when debugging is not needed
    # api_keys = [n for n in strings if __string_pipeline(n)]

    # Longer way to do this which makes it easier when debugging
    api_keys = []
    for string in strings:
        if __string_pipeline(string):
            api_keys.append(string)

    return api_keys


def detect_api_keys(strings: List[str]) -> List[bool]:
    """Detect api keys.

    Apply pre and post filtering of strings and return a list
    of bools with whether or not string was detected as api key.

    Args:

        strings (List[str]): List of strings to detect.

    Returns:

        List[bool]: List containing api classification status.
    """

    # List comprehension when debugging is not needed
    all_status = [__string_pipeline(n) for n in strings]

    # Longer way to do this which makes it easier when debugging
    # all_status = []
    # for string in strings:
    #     status = __string_pipeline(string)
    #     all_status.append(status)

    return all_status
