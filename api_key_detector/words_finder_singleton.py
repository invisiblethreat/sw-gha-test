"""
Singleton implementation for WordsFinder object
"""

from api_key_detector.words_finder import WordsFinder

def __get_module_path() -> str:
    import os
    basepath = os.path.dirname(os.path.realpath(__file__))
    return basepath

__get_full_path = lambda fname: f"{__get_module_path()}/{fname}"

wordlists = [
    'datasets/english_wordlist.txt',
    'datasets/computer_wordlist.txt',
]

finder = WordsFinder([__get_full_path(filename) for filename in wordlists])
