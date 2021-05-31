"""Utils"""

import time
from typing import List, Tuple, Union


def seconds_to_human(seconds: Union[int, float]) -> str:
    """Convert seconds to human readable time.

    Args:

        seconds (int): Number of seconds.

    Returns:

        str: String containing a human readable format of seconds.
    """

    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%dh%02dm%02ds" % (h, m, s)

def delta_seconds(start_time: Union[int, float]) -> float:
    """Calculate the difference in seconds between now and start_time.

    Args:

        start_time (int or float): Starting time in epoch seconds.

    Returns:

        float: Difference in seconds between now and start_time.
    """

    return time.time() - start_time

def human_delta(start_time: Union[int, float]) -> str:
    """Return a human readable delta between now and start_time.

    Args:

        start_time (int or float): Starting time in epoch seconds.

    Returns:

        str: Human readable delta between now and start_time.
    """

    return seconds_to_human(delta_seconds(start_time))

def map_bitmap(value: int, mapping: Tuple[int, str]) -> List[int]:
    """Returns values back from a bitmap.

    Args:

        value (int): The value to test.
        mapping (tuple): Mappings with values and strings to test against.

    Returns:

        List. List of items that matched against value.

    Example Usage:

    >>> map_feature = (
    ...             (0x1, 'planes'),
    ...             (0x2, 'trains'),
    ...             (0x4, 'automobiles')
    ...         )
    >>> map_bitmap(3, map_feature)
    [1, 2, 0]
    >>> map_bitmap(2, map_feature)
    [2, 0, 0]

    Example Code:

    r = map_bitmap(bitmap_mode, map_with_features)

    if 0x1 in r:
        i.planes = True
    if 0x2 in r:
        i.trains = True
    if 0x4 in r:
        i.automobiles = True

    """

    return [value & t[0] for t in mapping]

def format_like_uuid(value: str) -> str:
    """Formats a hex string like a UUID.

    Args:

        value (str): The string to convert to UUID format.

    Returns:

        str: UUID formatted string.

    Example Usage:

    >>> format_like_uuid("123e4567e89b12d3a456426655440000")
    '123e4567-e89b-12d3-a456-426655440000'

    """
    # In its canonical textual representation, the sixteen octets of a UUID are
    # represented as 32 hexadecimal (base 16) digits, displayed in five groups
    # separated by hyphens, in the form 8-4-4-4-12 for a total of 36 characters
    # (32 alphanumeric characters and four hyphens). For example:
    # 123e4567-e89b-12d3-a456-426655440000
    # xxxxxxxx-xxxx-Mxxx-Nxxx-xxxxxxxxxxxx
    # The four bits of digit M indicate the UUID version, and the one
    # to three most significant bits of digit N indicate the UUID variant.
    # In the example, M is 1 and N is a (10xx), meaning that the UUID is a
    # variant 1, version 1 UUID; that is, a time-based DCE/RFC 4122 UUID.
    # The canonical 8-4-4-4-12 format string is based on the "record layout"
    # for the 16 bytes of the UUID:[2]
    parts = lambda x: [x[:8], x[8:12], x[12:16], x[16:20], x[20:]]
    return '-'.join(parts(value.decode('ascii')))
