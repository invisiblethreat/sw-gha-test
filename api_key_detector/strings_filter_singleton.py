"""
Singleton implementation for WordsFinder object
"""

from api_key_detector.strings_filter import StringsFilter

def __get_module_path() -> str:
    import os
    basepath = os.path.dirname(os.path.realpath(__file__))
    return basepath

__get_full_path = lambda filename: f"{__get_module_path()}/{filename}"

blacklists = [
    'datasets/keys/blacklist.txt',
    'datasets/keys/manually_verified_keys.txt',
]

MIN_KEY_LENGTH = 16
MAX_KEY_LENGTH = 600
WORD_CONTENT_THRESHOLD = 0.4

s_filter = StringsFilter(MIN_KEY_LENGTH, MAX_KEY_LENGTH, WORD_CONTENT_THRESHOLD, [__get_full_path(filename) for filename in blacklists])
